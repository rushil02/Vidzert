from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
from .models import StaffProfile
from django.contrib.auth.models import Group
from admin_custom.models import ErrorLog


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def extend_staff(sender, **kwargs):
    if kwargs.get('created', True):
        user = kwargs.get('instance')
        if user.user_type in ('S', 'A'):
            group = Group.objects.get(name='Staff')
            user.groups.add(group)
            try:
                StaffProfile.objects.create(staff_id=user)
            except:
                error_meta = {
                    "method": "staff.signals.extend_staff",
                }
                ErrorLog.objects.create_log(error_code=1022, error_type='Staff Profile object creation failed',
                                            error_meta=error_meta)
