from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
from .models import (
    PromoterProfile, PromoterAccount
)
from django.contrib.auth.models import Group
from django.db import transaction
from admin_custom.models import ErrorLog


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def extend_promoter(sender, **kwargs):
    if kwargs.get('created', True):
        user = kwargs.get('instance')
        if user.user_type in ('P', 'A'):
            group = Group.objects.get(name='Promoter')
            user.groups.add(group)
            try:
                with transaction.atomic():
                    promoter_profile = PromoterProfile.objects.create(promoter_id=user)
                    PromoterAccount.objects.create(promoter_id=promoter_profile)
            except:
                error_meta = {
                    "method": "promoter.signals.extend_promoter",
                }
                ErrorLog.objects.create_log(error_code=1021, error_type='Promoter Profile object creation failed',
                                            error_meta=error_meta)
