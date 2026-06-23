# events/admin.py

from django.contrib import admin
from .models import Event, Seat, Booking


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "venue", "date", "status", "total_capacity", "price"]
    list_filter = ["status"]
    search_fields = ["title", "venue"]


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ["event", "row", "number", "status", "locked_by", "locked_at"]
    list_filter = ["status"]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["user", "seat", "status", "payment_reference", "created_at"]
    list_filter = ["status"]