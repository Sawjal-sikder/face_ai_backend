from rest_framework import serializers
from .models import Plan, Subscription

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = "__all__"
        read_only_fields = ("stripe_price_id",)
        
class PlanUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ["name", "interval", "amount", "trial_days", "active", "analyses_per_interval"]

class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = "__all__"
        read_only_fields = (
            "user",
            "stripe_customer_id",
            "stripe_subscription_id",
            "status",
            "trial_end",
            "current_period_end",
            "created_at",
            "updated_at",
        )