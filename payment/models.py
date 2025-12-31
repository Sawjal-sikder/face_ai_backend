# billing/models.py

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Plan(models.Model):
    name = models.CharField(max_length=50)
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_price_id = models.CharField(max_length=255)
    # amount = models.PositiveIntegerField(default=0)
    amount = models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    interval = models.CharField(max_length=20, choices=(("month", "Month"), ("year", "Year")))
    trial_days = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    # ANALYSIS CREDITS
    analyses_per_interval = models.IntegerField(default=0)
    # 1 = basic | 3 = standard | -1 = unlimited

    class Meta:
        ordering = ['-id']

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
            ("unpaid", "Unpaid"),
        ]
    )

    trial_end = models.DateTimeField(blank=True, null=True)
    current_period_end = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_active(self):
        return self.status in ["trialing", "active"]

    def is_trial(self):
        """Check if subscription is in trial period"""
        return self.status == "trialing"
    
    def is_paid_active(self):
        """Check if subscription is active (not trial)"""
        return self.status == "active"

    @classmethod
    def get_user_active_subscription(cls, user):
        return cls.objects.filter(
            user=user, status__in=["active", "trialing"]
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


class analysesBalance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="analyses_balances")
    balance = models.IntegerField(default=0)  # Number of analyses available
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - Balance: {self.balance}"
