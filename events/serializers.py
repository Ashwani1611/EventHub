from rest_framework import serializers
from .models import Event, Seat, Booking


class SeatSerializer(serializers.ModelSerializer):

    class Meta:
        model = Seat
        fields = ["id", "row", "number", "status"]


class EventSerializer(serializers.ModelSerializer):
    seats = SeatSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = [
            "id", "title", "description", "venue",
            "date", "total_capacity", "price", "status", "seats"
        ]


class BookingSerializer(serializers.ModelSerializer):
    seat = SeatSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = ["id", "seat", "status", "payment_reference", "created_at"]