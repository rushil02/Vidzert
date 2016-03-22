from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
from .models import ClientProfile
from django.contrib.auth.models import Group
from admin_custom.models import ErrorLog


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def extend_client(sender, **kwargs):
    if kwargs.get('created', True):
        user = kwargs.get('instance')
        if user.user_type in ('C', 'A'):
            group = Group.objects.get(name='Client')
            user.groups.add(group)
            try:
                ClientProfile.objects.create(client_id=user)
            except:
                error_meta = {
                    "method": "client.signals.extend_client",
                }
                ErrorLog.objects.create_log(error_code=1023, error_type='Client Profile object creation failed',
                                            error_meta=error_meta)
