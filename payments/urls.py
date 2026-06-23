from django.urls import path
from .views import CreatePaymentOrderView, RazorpayWebhookView

urlpatterns = [
    path("orders/<int:booking_id>/", CreatePaymentOrderView.as_view()),
    path("webhook/", RazorpayWebhookView.as_view()),
]