# from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

# class MySocialAccountAdapter(DefaultSocialAccountAdapter):
#     def save_user(self, request, sociallogin, form=None):
#         user = sociallogin.user
#         # Set is_active to True explicitly here
#         if user.pk is None:  # New user being created
#             user.is_active = True
#         user.save()
#         return user




from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Check if a user with the same email exists
        email_address = sociallogin.user.email

        if email_address:
            try:
                user = User.objects.get(email=email_address)
                sociallogin.connect(request, user)  # Connect the social account to the existing user
            except User.DoesNotExist:
                pass  # Let allauth handle it if no user is found

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        user.is_active = True
        user.save()
        return user
