# events/views.py

import logging
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Event, Seat, Booking
from .serializers import EventSerializer, SeatSerializer, BookingSerializer
from .lock_service import acquire_seat_lock, release_seat_lock

logger = logging.getLogger(__name__)


class EventListView(generics.ListAPIView):
    """Public — list all published events."""
    serializer_class = EventSerializer
    permission_classes = []

    def get_queryset(self):
        return Event.objects.filter(
            status=Event.Status.PUBLISHED
        ).prefetch_related("seats")


class EventDetailView(generics.RetrieveAPIView):
    """Public — retrieve a single event with its seats."""
    serializer_class = EventSerializer
    permission_classes = []

    def get_queryset(self):
        return Event.objects.filter(
            status=Event.Status.PUBLISHED
        ).prefetch_related("seats")


class LockSeatView(APIView):
    """
    Authenticated — lock a seat for the requesting user.
    Acquires Redis lock and marks seat as LOCKED in DB.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, seat_id):
        try:
            seat = Seat.objects.select_related("event").get(id=seat_id)
        except Seat.DoesNotExist:
            return Response(
                {"error": "Seat not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if seat.status != Seat.Status.AVAILABLE:
            return Response(
                {"error": "Seat is not available."},
                status=status.HTTP_409_CONFLICT
            )

        acquired = acquire_seat_lock(seat.id, request.user.id)

        if not acquired:
            return Response(
                {"error": "Seat is already locked by another user."},
                status=status.HTTP_409_CONFLICT
            )

        # Mark seat as locked in DB
        seat.status = Seat.Status.LOCKED
        seat.locked_by = request.user
        seat.locked_at = timezone.now()
        seat.save(update_fields=["status", "locked_by", "locked_at"])

        return Response(
            {
                "message": "Seat locked successfully. You have 10 minutes to complete checkout.",
                "seat": SeatSerializer(seat).data,
            },
            status=status.HTTP_200_OK
        )


class ReleaseSeatView(APIView):
    """
    Authenticated — release a seat lock held by the requesting user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, seat_id):
        try:
            seat = Seat.objects.get(id=seat_id, locked_by=request.user)
        except Seat.DoesNotExist:
            return Response(
                {"error": "Seat not found or not locked by you."},
                status=status.HTTP_404_NOT_FOUND
            )

        released = release_seat_lock(seat.id, request.user.id)

        if not released:
            return Response(
                {"error": "Could not release lock."},
                status=status.HTTP_400_BAD_REQUEST
            )

        seat.status = Seat.Status.AVAILABLE
        seat.locked_by = None
        seat.locked_at = None
        seat.save(update_fields=["status", "locked_by", "locked_at"])

        return Response(
            {"message": "Seat released successfully."},
            status=status.HTTP_200_OK
        )


class CreateBookingView(APIView):
    """
    Authenticated — confirm a booking for a locked seat.
    Called after payment is initiated (Phase 4 will extend this).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, seat_id):
        try:
            seat = Seat.objects.get(
                id=seat_id,
                locked_by=request.user,
                status=Seat.Status.LOCKED
            )
        except Seat.DoesNotExist:
            return Response(
                {"error": "Seat not found or not locked by you."},
                status=status.HTTP_404_NOT_FOUND
            )

        if Booking.objects.filter(seat=seat).exists():
            return Response(
                {"error": "Booking already exists for this seat."},
                status=status.HTTP_409_CONFLICT
            )

        booking = Booking.objects.create(
            user=request.user,
            seat=seat,
            status=Booking.Status.PENDING,
        )

        # Mark seat as booked
        seat.status = Seat.Status.BOOKED
        seat.save(update_fields=["status"])

        return Response(
            BookingSerializer(booking).data,
            status=status.HTTP_201_CREATED
        )


class MyBookingsView(generics.ListAPIView):
    """Authenticated — list all bookings for the requesting user."""
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user
        ).select_related("seat", "seat__event")