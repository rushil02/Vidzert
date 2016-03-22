from __future__ import absolute_import

import smtplib
import socket

from Vidzert.celery import app

from django.core.mail import send_mail
from admin_custom.models import ErrorLog

from .views_2 import log_error


@app.task(bind=True, name='send_single_mail', max_retries=10, default_retry_delay=600,
          throws=(smtplib.SMTPException, socket.error))
def send_mail_async(self, subject, message, recipients, from_email='no-reply@Vidzert.com', fail_silently=False):
    try:
        send_mail(subject, message, from_email, recipients, fail_silently)
    except (smtplib.SMTPException, socket.error) as e:
        error_meta = {'subject': subject, 'recipients': str(recipients)}
        ErrorLog.objects.create_log(6125, "Mailing Failed", error_meta, None)
        raise self.retry(exc=e)


# TODO: Hire API Service
@app.task(bind=True, name='send_single_sms', max_retries=10, default_retry_delay=600,
          throws=(socket.error,))
def send_sms_async(self, message, mobile_num):
    pass
