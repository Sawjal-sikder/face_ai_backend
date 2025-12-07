from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Plan(models.Model):
    name = models.CharField(max_length=50)
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True)  
    stripe_price_id = models.CharField(max_length=255)
    amount = models.PositiveIntegerField(default=0)  
    interval = models.CharField(max_length=20, choices=(("month", "Month"), ("year", "Year")))
    trial_days = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.interval}) - ${self.amount / 100}"



class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=50, 
        default="pending",
        choices=[
            ("pending", "Pending"),
            ("trialing", "Trialing"), 
            ("active", "Active"),
            ("past_due", "Past Due"),
            ("canceled", "Canceled"),
            ("unpaid", "Unpaid")
        ]
    )  # pending → trialing → active → canceled
    trial_end = models.DateTimeField(blank=True, null=True)
    current_period_end = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_active(self):
        return self.status in ["trialing", "active"]

    def is_trial(self):
        return self.status == "trialing"

    def is_paid_active(self):
        return self.status == "active"

    @classmethod
    def get_user_active_subscription(cls, user):
        """Get user's active subscription (trialing or active)"""
        return cls.objects.filter(
            user=user, 
            status__in=['trialing', 'active']
        ).first()

    def __str__(self):
        return f"{self.user} - {self.plan.name if self.plan else 'N/A'} ({self.status})"



class WebhookEvent(models.Model):
    event_id = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=255)
    data = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.event_id}"