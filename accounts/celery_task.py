from django.core.mail import send_mail
from django.conf import settings
from celery import shared_task

@shared_task
def Celery_send_mail(email, message, subject):
      send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])