from rest_framework import permissions
from .models import Subscription
from rest_framework.exceptions import APIException
from rest_framework import status

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
        active_subscription = Subscription.get_user_active_subscription(user)
        if active_subscription:
            return True

        raise SubscriptionRequired()