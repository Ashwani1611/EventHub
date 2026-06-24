import hmac
import hashlib

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings

from events.models import Event, Seat, Booking
from events.lock_service import acquire_seat_lock, release_seat_lock, get_lock_owner, _broadcast_current_seat_status
from payments.models import Payment
from payments.services import create_payment_order

User = get_user_model()


def home(request):
    events = Event.objects.all().order_by('date')
    return render(request, 'home.html', {'events': events})


def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    seats = event.seats.all().order_by('row', 'number')
    return render(request, 'events/detail.html', {'event': event, 'seats': seats})


@login_required(login_url='/accounts/login/')
def confirm_booking(request, seat_id):
    seat = get_object_or_404(Seat, id=seat_id)

    if request.method == 'GET':
        if seat.status == 'booked':
            messages.error(request, 'This seat has already been booked.')
            return redirect('frontend:event_detail', event_id=seat.event.id)

        owner = get_lock_owner(seat.id)

        if owner is not None and owner != str(request.user.id):
            # Someone else is actively holding this seat right now
            messages.error(request, 'This seat is currently being held by another user.')
            return redirect('frontend:event_detail', event_id=seat.event.id)

        if owner is None:
            # Nobody holds it — try to acquire it for this user
            acquired = acquire_seat_lock(seat.id, request.user.id)
            if not acquired:
                # Lost a race to another request between the check above and now
                messages.error(request, 'This seat was just taken by another user.')
                return redirect('frontend:event_detail', event_id=seat.event.id)
            seat.status = 'locked'
            seat.save()
            _broadcast_current_seat_status(seat.id)

        # If owner == this user already (e.g. page refresh), just fall through
        return render(request, 'bookings/confirm.html', {'seat': seat})

    # POST — re-verify this user still actually holds the lock before booking
    owner = get_lock_owner(seat.id)
    if owner != str(request.user.id):
        messages.error(request, 'Your hold on this seat expired. Please try again.')
        return redirect('frontend:event_detail', event_id=seat.event.id)

    booking, created = Booking.objects.get_or_create(
        user=request.user,
        seat=seat,
        defaults={'status': 'pending'}
    )

    payment = create_payment_order(booking)

    return render(request, 'payments/checkout.html', {
        'booking': booking,
        'order_id': payment.razorpay_order_id,
        'amount': int(payment.amount * 100),
        'razorpay_key': settings.RAZORPAY_KEY_ID,
    })


@login_required(login_url='/accounts/login/')
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related(
        'seat__event'
    ).order_by('-created_at')
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})


@login_required(login_url='/accounts/login/')
def payment_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    razorpay_payment_id = request.GET.get('razorpay_payment_id')
    razorpay_order_id   = request.GET.get('razorpay_order_id')
    razorpay_signature  = request.GET.get('razorpay_signature')

    verified = False

    if razorpay_payment_id and razorpay_order_id and razorpay_signature:
        body = f"{razorpay_order_id}|{razorpay_payment_id}"

        expected = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

        if hmac.compare_digest(expected, razorpay_signature):
            verified = True
            try:
                payment = Payment.objects.get(booking=booking)
                payment.razorpay_payment_id = razorpay_payment_id
                payment.status = 'paid'
                payment.save()

                booking.status = 'confirmed'
                booking.save()

                booking.seat.status = 'booked'
                booking.seat.save()
                _broadcast_current_seat_status(booking.seat.id)

                release_seat_lock(booking.seat.id, request.user.id)
            except Payment.DoesNotExist:
                verified = False

    if not verified:
        messages.error(request, "We couldn't verify this payment.")
        return redirect('frontend:payment_failed', booking_id=booking.id)

    return render(request, 'payments/success.html', {'booking': booking})


@login_required(login_url='/accounts/login/')
def payment_failed(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    booking.seat.status = 'available'
    booking.seat.save()
    _broadcast_current_seat_status(booking.seat.id)
    release_seat_lock(booking.seat.id, request.user.id)
    return render(request, 'payments/failed.html', {'booking': booking})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('frontend:home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', '')
            return redirect(next_url if next_url else 'frontend:home')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('frontend:home')
    if request.method == 'POST':
        username = request.POST.get('username')
        email    = request.POST.get('email')
        password = request.POST.get('password')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        else:
            user = User.objects.create_user(
                username=username, email=email, password=password
            )
            login(request, user)
            return redirect('frontend:home')
    return render(request, 'accounts/register.html')


def logout_view(request):
    logout(request)
    return redirect('frontend:login')

@login_required(login_url='/accounts/login/')
def organizer_dashboard(request):
    if request.user.role != 'organizer':
        messages.error(request, 'Access denied. Organizer account required.')
        return redirect('frontend:home')

    events = Event.objects.filter(
        organizer=request.user
    ).prefetch_related('seats').order_by('-created_at')

    return render(request, 'organizer/dashboard.html', {'events': events})


@login_required(login_url='/accounts/login/')
def notifications_view(request):
    from notifications.models import Notification

    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')

    # Mark all as read
    notifications.filter(is_read=False).update(is_read=True)

    return render(request, 'notifications/notifications.html', {
        'notifications': notifications
    })