from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import HStoreField
from ipware.ip import get_real_ip


class ErrorLogManager(models.Manager):
    def get_queryset(self):
        return super(ErrorLogManager, self).get_queryset()

    def create_log(self, error_code, error_type, error_meta, request=None):
        if request:
            fingerprint = request.session.get("fingerprint")
            ip = get_real_ip(request)
            if request.user.is_authenticated():
                self.create(actor=request.user, actor_ip=ip, error_code=error_code,
                            actor_fingerprint=fingerprint, error_type=error_type,
                            error_meta=error_meta)
            else:
                self.create(actor_ip=ip, error_code=error_code,
                            actor_fingerprint=fingerprint, error_type=error_type,
                            error_meta=error_meta)
        else:
            self.create(error_code=error_code,
                        error_type=error_type,
                        error_meta=error_meta)


class ErrorLog(models.Model):
    error_code = models.PositiveSmallIntegerField()
    error_type = models.CharField(max_length=50)
    error_meta = HStoreField(blank=True, null=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)
    actor_ip = models.GenericIPAddressField(unpack_ipv4=True, blank=True, null=True)
    actor_fingerprint = models.CharField(max_length=64, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = ErrorLogManager()


class ActivityLogManager(models.Manager):
    def get_queryset(self):
        return super(ActivityLogManager, self).get_queryset()

    def create_log(self, request, action_type, act_meta):
        fingerprint = request.session.get("fingerprint")
        ip = get_real_ip(request)
        if request.user.is_authenticated():
            self.create(actor=request.user, actor_ip=ip,
                        actor_fingerprint=fingerprint, action_type=action_type,
                        act_meta=act_meta)
        else:
            self.create(actor_ip=ip,
                        actor_fingerprint=fingerprint, action_type=action_type,
                        act_meta=act_meta)


class ActivityLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)
    actor_ip = models.GenericIPAddressField(unpack_ipv4=True, blank=True, null=True)
    actor_fingerprint = models.CharField(max_length=64, blank=True, null=True)
    action_type = models.CharField(max_length=50)
    act_meta = HStoreField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = ActivityLogManager()


class VideoCompletionLog(models.Model):
    video_id = models.ForeignKey('video.Video')
    STATUS = (('Q', 'Not Verified'),
              ('P', 'Verification - Positive'),
              ('N', 'Verification - Negative')
              )
    verified = models.CharField(max_length=1, choices=STATUS, default='Q')
    false_views = models.PositiveIntegerField(default=0)
    create_time = models.DateTimeField(auto_now_add=True)


class SurveyCompletionLog(models.Model):
    survey_id = models.ForeignKey('survey.Survey')
    STATUS = (('Q', 'Not Verified'),
              ('P', 'Verification - Positive'),
              ('N', 'Verification - Negative')
              )
    verified = models.CharField(max_length=1, choices=STATUS, default='Q')
    false_views = models.PositiveIntegerField(default=0)
    create_time = models.DateTimeField(auto_now_add=True)
