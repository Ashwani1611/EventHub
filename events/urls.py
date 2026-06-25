from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.EventListView.as_view(), name="event-list"),
    path("search/", views.EventSearchView.as_view(), name="event-search"),
    path("<int:pk>/", views.EventDetailView.as_view(), name="event-detail"),
    path("seats/<int:seat_id>/lock/", views.LockSeatView.as_view(), name="seat-lock"),
    path("seats/<int:seat_id>/release/", views.ReleaseSeatView.as_view(), name="seat-release"),
    path("seats/<int:seat_id>/book/", views.CreateBookingView.as_view(), name="seat-book"),
    path("bookings/my/", views.MyBookingsView.as_view(), name="my-bookings"),
]