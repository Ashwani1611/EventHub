from django.contrib import admin
from .models import Payment, WebhookEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "id", "booking", "razorpay_order_id", "amount",
        "currency", "status", "created_at",
    ]
    list_filter = ["status", "currency"]
    search_fields = ["razorpay_order_id", "razorpay_payment_id", "booking__id"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ["id", "event_type", "event_id", "received_at"]
    list_filter = ["event_type"]
    search_fields = ["event_id"]
    readonly_fields = ["received_at"]