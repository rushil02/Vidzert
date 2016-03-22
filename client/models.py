from django.db import models
from django.conf import settings
import uuid

# Create your models here.


class ClientProfile(models.Model):
    client_id = models.OneToOneField(settings.AUTH_USER_MODEL)
    address = models.TextField(null=True)
    contact2 = models.CharField(max_length=10, null=True)
    website = models.URLField(blank=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.client_id.email

    def field_names(self):
        return self._meta.get_all_field_names()
