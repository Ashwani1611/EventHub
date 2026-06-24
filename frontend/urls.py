from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.home, name='home'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),
    path('bookings/', views.my_bookings, name='my_bookings'),
    path('bookings/confirm/<int:seat_id>/', views.confirm_booking, name='confirm_booking'),
    path('payments/success/<int:booking_id>/', views.payment_success, name='payment_success'),
    path('payments/failed/<int:booking_id>/', views.payment_failed, name='payment_failed'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/register/', views.register_view, name='register'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('organizer/dashboard/', views.organizer_dashboard, name='organizer_dashboard'),
    path('notifications/', views.notifications_view, name='notifications'),
]