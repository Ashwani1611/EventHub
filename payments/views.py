from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.conf import settings

from events.models import Booking
from .services import create_payment_order


class CreatePaymentOrderView(APIView):
    """
    POST /api/payments/orders/{booking_id}/
    Creates (or reuses) a Razorpay order for the given booking and
    returns everything the frontend needs to open Razorpay Checkout.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)

        payment = create_payment_order(booking)

        return Response({
            "order_id": payment.razorpay_order_id,
            "amount": int(payment.amount * 100),  # paise, what Checkout expects
            "currency": payment.currency,
            "key": settings.RAZORPAY_KEY_ID,
            "booking_id": booking.id,
        }, status=status.HTTP_200_OK)