from django.db import models
import uuid
from django.conf import settings

# Create your models here.


class VideoPromoterLogManager(models.Manager):
    def get_queryset(self):
        return super(VideoPromoterLogManager, self).get_queryset()

    def promoter_log_entry(self, video, promoter, ip, share_url, coins, position, device_type):
        return self.get_queryset().create(video_id=video, promoter_id=promoter, ip=ip, share_url=share_url, coins=coins, position=position, device_type=device_type)


class VideoPromoterLog(models.Model):
    video_id = models.ForeignKey('video.Video')
    promoter_id = models.ForeignKey('promoter.PromoterProfile')
    ip = models.GenericIPAddressField(unpack_ipv4=True, blank=True, null=True)
    share_url = models.URLField(max_length=2000)
    coins = models.PositiveIntegerField(default=0)
    position = models.PositiveIntegerField()
    DEVICE_TYPE = (
        ('C', 'Computer'),
        ('M', 'Mobile'),
    )
    device_type = models.CharField(max_length=1, choices=DEVICE_TYPE, blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True)

    objects = VideoPromoterLogManager()

    class Meta:
        unique_together = (('video_id', 'promoter_id'), ('video_id', 'position'))

    def __unicode__(self):
        return '%s by %s' % (self.video_id, self.promoter_id)


class VideoUnsubscribedLogManager(models.Manager):
    def get_queryset(self):
        return super(VideoUnsubscribedLogManager, self).get_queryset()

    def unsubsribed_log_entry(self, video, position, duration, promoter=None, ip=None, device_type=None, ad_clicked=False):
        return self.get_queryset().create(video_id=video, promoter_id=promoter, ip=ip, position=position, device_type=device_type, duration=duration, ad_clicked=ad_clicked)


class VideoUnsubscribedLog(models.Model):
    video_id = models.ForeignKey('video.Video')
    promoter_id = models.ForeignKey('promoter.PromoterProfile', blank=True, null=True)
    ip = models.GenericIPAddressField(unpack_ipv4=True, blank=True, null=True)
    position = models.PositiveIntegerField(blank=True, null=True)
    DEVICE_TYPE = (
        ('C', 'Computer'),
        ('M', 'Mobile'),
    )
    device_type = models.CharField(max_length=1, choices=DEVICE_TYPE, blank=True, null=True)
    duration = models.DecimalField(max_digits=10, decimal_places=6)
    ad_clicked = models.BooleanField(default=False)
    create_time = models.DateTimeField(auto_now_add=True)

    objects = VideoUnsubscribedLogManager()

    def __unicode__(self):
        return '%s' % self.video_id


class PerkTransactionLogManager(models.Manager):
    def get_queryset(self):
        return super(PerkTransactionLogManager, self).get_queryset()

    def perk_transaction_log_entry(self, promoter, perk):
        return self.get_queryset().create(promoter_id=promoter, perk_id=perk, eggs=perk.cost)


class PerkTransactionLog(models.Model):
    ref_no = models.CharField(max_length=10, unique=True, null=True, blank=True)  # TODO: change to null blank false
    promoter_id = models.ForeignKey('promoter.PromoterProfile')
    perk_id = models.ForeignKey('perks.Perks')
    eggs = models.PositiveIntegerField()
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    transaction_time = models.DateTimeField(auto_now_add=True)

    objects = PerkTransactionLogManager()

    def __unicode__(self):
        return self.ref_no


class GrayListManager(models.Manager):
    def get_queryset(self):
        return super(GrayListManager, self).get_queryset()

    def gray_list_entry(self, ip, promoter=None):
        self.get_queryset().craete(ip=ip, promoter_id=promoter)


class GrayList(models.Model):
    ip = models.GenericIPAddressField(unpack_ipv4=True, blank=True, null=True)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True)

    objects = GrayListManager()

    def __unicode__(self):
        if self.user_id is None:
            return self.ip
        else:
            return self.user_id


class BlackListManager(models.Manager):
    def get_queryset(self):
        return super(BlackListManager, self).get_queryset()

    def black_list_entry(self, ip, promoter=None):
        self.get_queryset().craete(ip=ip, promoter_id=promoter)


class BlackList(models.Model):
    ip = models.GenericIPAddressField(unpack_ipv4=True, blank=True, null=True)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True)

    objects = BlackListManager()

    def __unicode__(self):
        if self.user_id is None:
            return self.ip
        else:
            return self.user_id


class DurationWatchedLogManager(models.Manager):
    def get_queryset(self):
        return super(DurationWatchedLogManager, self).get_queryset()

    def duration_watch_log_entry(self, video, promoter, ip, duration, ad_clicked=False):
        return self.get_queryset().create(video_id=video, promoter_id=promoter, ip=ip, duration=duration, ad_clicked=ad_clicked)


class DurationWatchedLog(models.Model):
    video_id = models.ForeignKey('video.Video')
    promoter_id = models.ForeignKey('promoter.PromoterProfile')
    ip = models.GenericIPAddressField(unpack_ipv4=True, blank=True, null=True)
    duration = models.DecimalField(max_digits=10, decimal_places=6)
    ad_clicked = models.BooleanField(default=False)
    create_time = models.DateTimeField(auto_now_add=True)

    objects = DurationWatchedLogManager()

    def __unicode__(self):
        return self.video_id


class VideoPromoterReplayLogManager(models.Manager):
    def get_queryset(self):
        return super(VideoPromoterReplayLogManager, self).get_queryset()

    def replay_video_log_entry(self, video, promoter, ip, device_type):
        return self.get_queryset().create(video_id=video, promoter_id=promoter, ip=ip, device_type=device_type)


class VideoPromoterReplayLog(models.Model):
    video_id = models.ForeignKey('video.Video')
    promoter_id = models.ForeignKey('promoter.PromoterProfile')
    ip = models.GenericIPAddressField(unpack_ipv4=True, blank=True, null=True)
    DEVICE_TYPE = (
        ('C', 'computer'),
        ('M', 'Mobile'),
    )
    device_type = models.CharField(max_length=1, choices=DEVICE_TYPE, blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True)

    objects = VideoPromoterReplayLogManager()

    def __unicode__(self):
        return self.video_id


class VideoPromoterPerkLogManager(models.Manager):
    def get_queryset(self):
        return super(VideoPromoterPerkLogManager, self).get_queryset()

    def video_promoter_perk_log_entry(self, video, promoter, perk, quantity=1):
        return self.get_queryset().create(video_id=video, promoter_id=promoter, perk_id=perk, quantity=quantity)


class VideoPromoterPerkLog(models.Model):
    video_id = models.ForeignKey('video.Video')
    promoter_id = models.ForeignKey('promoter.PromoterProfile')
    perk_id = models.ForeignKey('perks.Perks')
    quantity = models.PositiveIntegerField(default=1)
    create_time = models.DateTimeField(auto_now_add=True)

    objects = VideoPromoterPerkLogManager()

    class Meta:
        unique_together = ('video_id', 'promoter_id', 'perk_id')


class SurveyPromoterLogManager(models.Manager):
    def get_queryset(self):
        return super(SurveyPromoterLogManager, self).get_queryset()

    def promoter_survey_log_entry(self, survey, promoter, ip, coins, position, device_type):
        return self.get_queryset().create(survey_id=survey, promoter_id=promoter, ip=ip, coins=coins,
                                          position=position, device_type=device_type)


class SurveyPromoterLog(models.Model):
    survey_id = models.ForeignKey('survey.Survey')
    promoter_id = models.ForeignKey('promoter.PromoterProfile')
    ip = models.GenericIPAddressField(unpack_ipv4=True, blank=True, null=True)
    coins = models.PositiveIntegerField(default=0)
    position = models.PositiveIntegerField()
    DEVICE_TYPE = (
        ('C', 'Computer'),
        ('M', 'Mobile'),
    )
    device_type = models.CharField(max_length=1, choices=DEVICE_TYPE, blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True)

    objects = SurveyPromoterLogManager()

    class Meta:
        unique_together = (('survey_id', 'promoter_id'), ('survey_id', 'position'))

    def __unicode__(self):
        return '%s by %s' % (self.survey_id, self.promoter_id)
