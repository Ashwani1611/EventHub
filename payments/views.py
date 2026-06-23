from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.conf import settings
import hmac
import hashlib
import json

from events.models import Booking, Seat
from .models import Payment, WebhookEvent
from .services import create_payment_order


class CreatePaymentOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        data = create_payment_order(booking)
        return Response(data, status=status.HTTP_200_OK)


class RazorpayWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # 1. Verify signature
        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        received_signature = request.headers.get("X-Razorpay-Signature", "")
        body = request.body

        expected_signature = hmac.new(
            webhook_secret.encode("utf-8"),
            body,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, received_signature):
            return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Parse payload
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)

        event_id = payload.get("id")
        event_type = payload.get("event")

        # 3. Idempotency check
        if WebhookEvent.objects.filter(event_id=event_id).exists():
            return Response({"status": "already processed"}, status=status.HTTP_200_OK)

        # 4. Store webhook event
        WebhookEvent.objects.create(
            event_id=event_id,
            event_type=event_type,
            payload=payload,
        )

        # 5. Handle events
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        razorpay_payment_id = payment_entity.get("id")
        razorpay_order_id = payment_entity.get("order_id")

        try:
            payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        if event_type == "payment.captured":
            payment.razorpay_payment_id = razorpay_payment_id
            payment.status = "paid"
            payment.save()

            booking = payment.booking
            booking.status = "confirmed"
            booking.save()

            seat = booking.seat
            seat.status = "booked"
            seat.save()

        elif event_type == "payment.failed":
            payment.razorpay_payment_id = razorpay_payment_id
            payment.status = "failed"
            payment.save()

        return Response({"status": "ok"}, status=status.HTTP_200_OK)