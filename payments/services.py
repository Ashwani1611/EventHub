import logging

import razorpay
from django.conf import settings
from django.db import transaction

from .models import Payment

logger = logging.getLogger(__name__)


def get_razorpay_client():
    """
    Single source of truth for the Razorpay SDK client.
    """
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


def create_payment_order(booking):
    """
    Creates a Razorpay order for a given Booking and persists a
    corresponding Payment row with status=CREATED.

    Idempotent: if a Payment already exists for this booking and
    hasn't failed, returns the existing one instead of creating a
    duplicate Razorpay order (avoids IntegrityError on the OneToOne
    constraint from double-clicks or retried requests).
    """
    existing = Payment.objects.filter(booking=booking).first()
    if existing and existing.status != Payment.Status.FAILED:
        logger.info(f"Reusing existing payment | payment_id={existing.id} | booking_id={booking.id}")
        return existing

    amount_rupees = booking.seat.event.price  # adjust if price lives on Seat instead
    amount_paise = int(amount_rupees * 100)

    client = get_razorpay_client()

    order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "receipt": f"booking_{booking.id}",
        "notes": {
            "booking_id": str(booking.id),
            "user_id": str(booking.user_id),
        },
    })

    with transaction.atomic():
        if existing:
            # Previous attempt failed — update it in place rather than
            # inserting a second row (OneToOneField forbids that anyway).
            existing.razorpay_order_id = order["id"]
            existing.amount = amount_rupees
            existing.status = Payment.Status.CREATED
            existing.save()
            payment = existing
        else:
            payment = Payment.objects.create(
                booking=booking,
                razorpay_order_id=order["id"],
                amount=amount_rupees,
                currency="INR",
                status=Payment.Status.CREATED,
            )

    logger.info(f"Razorpay order created | order_id={order['id']} | booking_id={booking.id}")

    return payment