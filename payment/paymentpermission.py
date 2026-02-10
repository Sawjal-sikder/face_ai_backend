from rest_framework import permissions, status #type: ignore
from rest_framework.exceptions import APIException #type: ignore
from .models import AnalysisCreditTransaction


class SubscriptionRequired(APIException):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = "Please purchase a subscription."
    default_code = "subscription_required"

class HasActiveSubscription(permissions.BasePermission):
    """
    Allows access only to users with active or trialing subscription.
    """

    message = "Please purchase a subscription."
    

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False

        # Use your Subscription model method
        active_balance = AnalysisCreditTransaction.get_balance(user)
        if active_balance > 0:
            return True

        raise SubscriptionRequired()