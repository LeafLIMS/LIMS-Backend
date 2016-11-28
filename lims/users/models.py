import random
import string
import smtplib

from django.db import models
from django.core.mail import send_mail
from django.conf import settings

from django.contrib.auth.models import User


def generate_code():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))


class ResetCode(models.Model):
    """
    Provide a code to reset a users forgotten details.
    """
    code = models.CharField(max_length=8, default=generate_code)
    account = models.ForeignKey(User)

    def send_email(self):
        if self.code and self.account:
            subject = '{from_name} user account access code'.format(from_name=settings.EMAIL_FROM)
            message = '''Dear {first} {last},\n
You are receiveing this email as you have asked to reset a part of your account.\n
Please input the following code when asked: {code}\n
Thank you,\n
{from_name}'''.format(first=self.account.first_name,
                      last=self.account.last_name,
                      code=self.code,
                      from_name=settings.EMAIL_FROM)
            try:
                send_mail(subject,
                          message,
                          settings.EMAIL_HOST_USER,
                          (self.account.email,),
                          fail_silently=False)
            except smtplib.SMTPException:
                return False
            return True
