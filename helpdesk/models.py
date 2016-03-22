from django.db import models
from django.conf import settings
import uuid
import os
import time


# Create your models here.


# Thumbnail file rename
def get_message_image_path(instance, filename):
    path = 'Helpdesk/Message_Image' + time.strftime('/%Y/%m/%d/')
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (instance.ticket.uuid, ext)
    return os.path.join(path, filename)


class Ticket(models.Model):
    submitter = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    submitter_email = models.EmailField(max_length=255)
    title = models.CharField(max_length=255)
    TICKET_TYPE = (
        ('C', 'Coins Not Transferred'),
        ('O', 'Other'),
    )
    ticket_type = models.CharField(max_length=1, choices=TICKET_TYPE)
    STATUS = (
        ('O', 'Open'),
        ('R', 'Resolved'),
        ('C', 'Closed')
    )
    status = models.CharField(max_length=1, choices=STATUS, default='O')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    ref_no = models.CharField(max_length=15, blank=True, default='')
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.title

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if self.pk is None:
            try:
                latest_obj = Ticket.objects.latest('id')
            except:
                latest_obj_id = 0
            else:
                latest_obj_id = latest_obj.id
            self.ref_no = "TIC%012d" % (latest_obj_id + 1)
        super(Ticket, self).save(force_insert, force_update, using, update_fields)


class Message(models.Model):
    ticket = models.ForeignKey(Ticket)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    SENDER_TYPE = (
        ('U', 'User'),
        ('A', 'Admin'),
    )
    sender_type = models.CharField(max_length=1, choices=SENDER_TYPE)
    message_text = models.TextField(max_length=512, blank=True, null=True)
    message_image = models.ImageField(upload_to=get_message_image_path, null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.ticket.title
