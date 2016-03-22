from django.db import models
from django.conf import settings
from datetime import date
import uuid
from django.db.models import Q, F
from video.models import Video
from survey.models import Survey


class PromoterProfileQuerySet(models.query.QuerySet):
    def get_from_uuid(self, promoter_uuid):
        return self.get(uuid=promoter_uuid)


class PromoterProfileManager(models.Manager):
    def get_queryset(self):
        return PromoterProfileQuerySet(self.model, using=self._db)

    def get_promoter(self, promoter_uuid):
        return self.get_queryset().get_from_uuid(promoter_uuid)

    def get_all_mail_recipients(self):
        email_list = []
        object_list = self.get_queryset().filter(promoteraccount__mail_notification_flag='A').select_related(
            'promoter_id')
        for promoter in object_list:
            email_list.append(promoter.promoter_id.email)
        return email_list


class PromoterProfile(models.Model):
    promoter_id = models.OneToOneField(settings.AUTH_USER_MODEL)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    GENDER = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    gender = models.CharField(max_length=1, choices=GENDER, blank=True, null=True)
    area_city = models.CharField(max_length=20, blank=True, null=True)
    area_state = models.ForeignKey('cities_light.Region', blank=True, null=True)
    PAN = models.CharField(max_length=10, unique=True, blank=True, null=True)
    promoter_category_profile = models.ManyToManyField('video.VideoCategory', through='Profiling')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    objects = PromoterProfileManager()

    def fetch_profiling_details(self):
        today = date.today()
        if self.dob:
            age = today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
            return age, self.gender, self.area_city, self.area_state
        else:
            return 0, self.gender, self.area_city, self.area_state

    def __unicode__(self):
        return self.promoter_id.email

    def promoter_profiling(self, entity_obj, profiling_type):
        # profiling type {
        # 1: Engagement
        # 2: view
        # 3: backlink
        # }

        categories = entity_obj.category.all()
        for category in categories:
            (promoter_profiling_obj, created) = Profiling.objects.get_or_create(promoter_id=self, category_id=category)
            if profiling_type == 1:
                promoter_profiling_obj.engagement += 1
            elif profiling_type == 2:
                promoter_profiling_obj.views += 1
            elif profiling_type == 3:
                promoter_profiling_obj.backlinks += 1
            elif profiling_type == 4:
                promoter_profiling_obj.survey_fills += 1
            promoter_profiling_obj.cal_score()

    def promoter_backlink(self, video):
        promoter_account = self.promoteraccount
        # increment eggs
        promoter_account.increment_account_eggs()

        # profiling
        self.promoter_profiling(video, 3)

    def check_video_watched(self, video):
        logs = self.videopromoterlog_set.filter(video_id=video)
        if logs:
            return True
        else:
            return False

    def check_survey_filled(self, survey):
        logs = self.surveypromoterlog_set.filter(survey_id=survey)
        if logs:
            return True
        else:
            return False

    def profile_v2(self):
        videos = []

        (age, gender, area_city, area_state) = self.fetch_profiling_details()
        promoter_categories = self.promoter_category_profile.all().order_by('-profiling__score')
        featured_profiled_category_videos = Video.objects.get_featured_profiled_category_videos(self,
                                                                                                promoter_categories,
                                                                                                age, gender, area_city,
                                                                                                area_state)

        profiled_category_videos = Video.objects.get_profiled_category_videos(self, promoter_categories, age, gender,
                                                                              area_city, area_state)

        # Priority #1 - featured category profiled
        videos.extend(featured_profiled_category_videos)
        # videos.extend(featured_everyone_category_videos)

        # Priority #2 - featured left profiled
        featured_left_videos = Video.objects.get_featured_profiled_videos(self, promoter_categories, age, gender,
                                                                          area_city, area_state)

        videos.extend(featured_left_videos)

        # Priority #3 - all category profiled
        videos.extend(profiled_category_videos)

        # Priority #4 - all left profiled
        all_profiled_videos = Video.objects.get_all_profiled_videos(self, promoter_categories, age, gender,
                                                                    area_city, area_state)

        videos.extend(all_profiled_videos)

        # Priority #5 - All featured non profiled
        all_featured_promoter_videos = Video.objects.get_all_featured_promoter_videos(self, age, gender, area_city,
                                                                                      area_state)

        videos.extend(all_featured_promoter_videos)

        # Priority #6 - All non profiled
        all_promoter_videos = Video.objects.get_all_promoter_videos(self, age, gender, area_city, area_state)
        videos.extend(all_promoter_videos)

        return videos

    def survey_profile(self):
        surveys = []

        (age, gender, area_city, area_state) = self.fetch_profiling_details()
        promoter_categories = self.promoter_category_profile.all().order_by('-profiling__score')
        profiled_category_surveys = Survey.objects.get_category_profiled_surveys(self, promoter_categories, age, gender,
                                                                                 area_city, area_state)
        surveys.extend(profiled_category_surveys)
        all_profiled_surveys = Survey.objects.get_all_profiled_surveys(self, promoter_categories, age, gender,
                                                                       area_city, area_state)
        surveys.extend(all_profiled_surveys)
        return surveys


class PromoterAccountManager(models.Manager):
    def get_queryset(self):
        return super(PromoterAccountManager, self).get_queryset()

    def set_mail_notification_flag(self):
        return self.get_queryset().filter(mail_notification_flag='A').update(mail_notification_flag='')


class PromoterAccount(models.Model):
    promoter_id = models.OneToOneField(PromoterProfile)
    current_coins = models.PositiveIntegerField(default=0)
    current_eggs = models.PositiveIntegerField(default=0)
    total_coins = models.PositiveIntegerField(default=0)
    total_eggs = models.PositiveIntegerField(default=0)
    MAIL_CHOICES = (
        ('A', 'Advanced Notification'),
        ('L', 'Locate Highest Peak'),
    )
    mail_notification_flag = models.CharField(max_length=1, choices=MAIL_CHOICES, blank=True, null=True)
    perks = models.ManyToManyField('perks.Perks', through='PromoterPerks', blank=True)
    penalty_weight = models.PositiveSmallIntegerField(default=0)
    penalty_decay_ref = models.PositiveIntegerField(default=0)
    update_time = models.DateTimeField(auto_now=True)

    objects = PromoterAccountManager()

    def __unicode__(self):
        return self.promoter_id.promoter_id.email

    def get_promoter_perk(self):
        return "\n".join([p.name for p in self.perks.all()])

    def get_perks(self):
        return self.promoterperks_set.filter(~Q(quantity=0)).select_related('perk_id')

    def get_graph_perks(self):
        pre_perks = []
        post_perks = []
        perks = self.promoterperks_set.filter(Q(perk_id__block='F') | Q(perk_id__block='L'),
                                              quantity__gt=0).select_related('perk_id')
        for perk in perks:
            if perk.perk_id.block == 'F':
                pre_perks.append(perk)
            elif perk.perk_id.block == 'L':
                post_perks.append(perk)
        return pre_perks, post_perks

    def increment_account_coins(self, coins):
        self.current_coins += coins
        self.total_coins += coins
        self.save()

    def increment_account_eggs(self):
        self.current_eggs += 1
        self.total_eggs += 1
        self.save()

    def decrement_promoter_eggs(self, eggs):
        self.current_eggs -= eggs
        self.save()

    def increment_promoter_perk(self, perk):
        (promoter_perk_obj, created) = PromoterPerks.objects.get_or_create(promoter_id=self, perk_id=perk)
        promoter_perk_obj.quantity += 1
        promoter_perk_obj.save()

    def decrement_account_coins(self, coins):
        self.current_coins -= coins
        self.save()


class Profiling(models.Model):
    promoter_id = models.ForeignKey(PromoterProfile)
    category_id = models.ForeignKey('video.VideoCategory')
    backlinks = models.PositiveIntegerField(default=0)
    engagement = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    survey_fills = models.PositiveIntegerField(default=0)
    score = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('promoter_id', 'category_id')

    def cal_score(self):
        self.score = (self.backlinks * 0.66) + (self.engagement * 1) + (self.views * 0.33)
        self.save()

    def __unicode__(self):
        return 'Profile: %s with Category: %s' % (self.promoter_id.promoter_id.email, self.category_id.category_name)


class PromoterPerks(models.Model):
    promoter_id = models.ForeignKey(PromoterAccount)
    perk_id = models.ForeignKey('perks.Perks')
    quantity = models.PositiveIntegerField(default=0)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('promoter_id', 'perk_id')

    def __unicode__(self):
        return 'Profile: %s with Perk: %s' % (self.promoter_id.promoter_id.promoter_id.email, self.perk_id.name)

    def decrement_perk_quantity(self, quantity=1):
        self.quantity -= quantity
        self.save()
