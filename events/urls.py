from django.urls import path
from .views import (
    EventListView,
    EventDetailView,
    LockSeatView,
    ReleaseSeatView,
    CreateBookingView,
    MyBookingsView,
)

app_name = "events"

urlpatterns = [
    path("", EventListView.as_view(), name="event-list"),
    path("<int:pk>/", EventDetailView.as_view(), name="event-detail"),

    path("seats/<int:seat_id>/lock/", LockSeatView.as_view(), name="seat-lock"),
    path("seats/<int:seat_id>/release/", ReleaseSeatView.as_view(), name="seat-release"),

    path("bookings/", CreateBookingView.as_view(), name="booking-create"),
    path("bookings/my/", MyBookingsView.as_view(), name="my-bookings"),
]