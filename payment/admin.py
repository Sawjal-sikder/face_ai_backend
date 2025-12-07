from django.contrib import admin
from .models import Plan, Subscription, WebhookEvent


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "interval", "amount", "active")
    list_filter = ("interval", "active")
    search_fields = ("name", "stripe_product_id", "stripe_price_id")
    readonly_fields = ("stripe_product_id",)  # optional
    ordering = ("amount",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "plan",
        "status",
        "stripe_customer_id",
        "stripe_subscription_id",
        "trial_end",
        "current_period_end",
        "created_at",
    )
    list_filter = ("status", "plan")
    search_fields = (
        "user__username",
        "user__email",
        "stripe_customer_id",
        "stripe_subscription_id",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "type", "received_at")
    search_fields = ("event_id", "type")
    readonly_fields = ("event_id", "type", "data", "received_at")
    ordering = ("-received_at",)
