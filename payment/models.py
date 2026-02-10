from django.db import models #type: ignore
from django.contrib.auth import get_user_model #type: ignore
from django.db.models import Sum #type: ignore

User = get_user_model()


class Plan(models.Model):
    name = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    interval = models.CharField(max_length=20, choices=(("month", "Month"), ("year", "Year")))
    active = models.BooleanField(default=True)
    # ANALYSIS CREDITS
    credits = models.IntegerField(default=0)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.name} ({self.interval})"
    
    
class PaypalEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="paypal_events")
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    credits = models.IntegerField(default=0)
    event_response = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"PaypalEvent for {self.user} - Plan: {self.plan.name}"





class AnalysisCreditTransaction(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="analysis_credit_transactions"
    )
    credits = models.IntegerField(default=1)
    type = models.CharField(max_length=50, default="use")  # purchase / use
    reason = models.CharField(max_length=255, default="Use for analysis")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.type} - {self.credits}"

    @staticmethod
    def get_balance(user):
        purchase_total = (
            AnalysisCreditTransaction.objects
            .filter(user=user, type="purchase")
            .aggregate(total=Sum("credits"))["total"]
            or 0
        )

        use_total = (
            AnalysisCreditTransaction.objects
            .filter(user=user, type="use")
            .aggregate(total=Sum("credits"))["total"]
            or 0
        )

        return purchase_total - use_total