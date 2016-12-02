from django.core.mail import send_mail
from django.conf import settings


def send_email(message):
    send_mail(
        message['title'],
        message['content'],
        settings.EMAIL_HOST_USER,
        message['recipients'],
        fail_silently=True,
    )
