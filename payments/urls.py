from django.urls import path
from .views import CreatePaymentOrderView

app_name = "payments"

urlpatterns = [
    path("orders/<int:booking_id>/", CreatePaymentOrderView.as_view(), name="create-order"),
]