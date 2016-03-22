from django.contrib.postgres.fields.hstore import HStoreField
from django.db import models
from django.contrib.postgres.fields import IntegerRangeField
import uuid
from django.template.defaultfilters import slugify
import datetime
import os
import time
from django.db.models import Q
from admin_custom.models import VideoCompletionLog


# Video file rename
def get_video_file_path(instance, filename):
    path = 'Video' + time.strftime('/%Y/%m/%d/') + 'Original'
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (instance.video_id.uuid, ext)
    return os.path.join(path, filename)


# Thumbnail file rename
def get_thumbnail_file_path(instance, filename):
    path = 'Video' + time.strftime('/%Y/%m/%d/') + 'Thumbnails'
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (instance.video_id.uuid, ext)
    return os.path.join(path, filename)


# Banner image file rename
def get_banner_file_path(instance, filename):
    path = 'Video' + time.strftime('/%Y/%m/%d/') + 'Banners'
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (instance.video_id.uuid, ext)
    return os.path.join(path, filename)


# Create your models here.
class VideoQuerySet(models.query.QuerySet):
    def active(self):
        return self.filter(active=True)

    def featured(self):
        return self.filter(featured=True)

    def get_from_uuid(self, video_uuid):
        return self.get(uuid=video_uuid)

    def get_from_slug(self, video_slug):
        return self.get(slug=video_slug)

    def not_paid(self):
        return self.filter(videostatus__active=True, videostatus__current__in=['IF', 'EP'])

    def not_authorised(self):
        return self.filter(~Q(videostatus__current='AA'), videostatus__active=True)

    def exclude_promoter(self, promoter):
        return self.exclude(videopromoterlog__promoter_id=promoter)

    def profiled(self, age, gender, area_city, area_state):
        return self.filter(Q(videoprofile__age__contains=age),
                           Q(videoprofile__gender=gender) | Q(videoprofile__gender='A'),
                           Q(videoprofile__state=area_state) | Q(videoprofile__state=None))

    def exclude_featured(self):
        return self.exclude(featured=True)

    def exclude_categories(self, promoter_categories):
        return self.filter(~Q(category__in=promoter_categories))

    def include_categories(self, promoter_categories):
        return self.filter(category__in=promoter_categories)

    def select_for_display(self):
        return self.select_related('videofile__thumbnail_image') \
            .values('videofile__thumbnail_image', 'name', 'max_coins', 'publisher', 'uuid', 'slug') \
            .order_by('update_time')

    def not_profiled(self, age, gender, area_city, area_state):
        return self.filter(~Q(videoprofile__age__contains=age) |
                           Q(~Q(videoprofile__gender=gender) & ~Q(videoprofile__gender='A')) |
                           Q(~Q(videoprofile__state=area_state) & ~Q(videoprofile__state=None)))

    def everyone(self):
        return self.filter(videoprofile__age__startswith=0, videoprofile__age__endswith=150,
                           videoprofile__gender='A',
                           videoprofile__state=None)

    def not_everyone(self):
        return self.filter(~Q(videoprofile__age__startswith=0) | ~Q(videoprofile__age__endswith=150) |
                           ~Q(videoprofile__gender='A') |
                           ~Q(videoprofile__state=None))


class VideoManager(models.Manager):
    def get_queryset(self):
        return VideoQuerySet(self.model, using=self._db)

    def get_featured(self):
        return self.get_queryset().featured().active()

    def get_active(self):
        return self.get_queryset().active()

    def get_video_playback(self, video_uuid):
        return self.get_queryset().select_related('videoinfo', 'videofile').get_from_uuid(video_uuid)

    def get_video(self, video_uuid):
        return self.get_queryset().get_from_uuid(video_uuid)

    def get_video_from_slug(self, video_slug):
        return self.get_queryset().get_from_slug(video_slug)

    def get_non_authorised_videos(self):
        return self.get_queryset().not_paid().not_authorised()

    def get_non_paid_videos(self):
        return self.get_queryset().not_paid()

    def get_featured_profiled_videos(self, promoter, promoter_categories, age, gender, area_city, area_state):
        return self.get_featured().exclude_promoter(promoter).profiled(age, gender, area_city,
                                                                       area_state) \
            .exclude_categories(promoter_categories) \
            .select_for_display()

    def get_all_profiled_videos(self, promoter, promoter_categories, age, gender, area_city, area_state):
        return self.get_active().exclude_featured().exclude_promoter(promoter) \
            .profiled(age, gender, area_city, area_state) \
            .exclude_categories(promoter_categories) \
            .select_for_display()

    def get_featured_profiled_category_videos(self, promoter, promoter_categories, age, gender, area_city, area_state):
        return self.get_featured().exclude_promoter(promoter) \
            .include_categories(promoter_categories) \
            .profiled(age, gender, area_city, area_state) \
            .select_for_display()

    def get_profiled_category_videos(self, promoter, promoter_categories, age, gender, area_city, area_state):
        return self.get_active().exclude_featured().exclude_promoter(promoter) \
            .include_categories(promoter_categories) \
            .profiled(age, gender, area_city, area_state) \
            .select_for_display()

    def get_all_featured_promoter_videos(self, promoter, age, gender, area_city, area_state):
        return self.get_featured().exclude_promoter(promoter) \
            .not_profiled(age, gender, area_city, area_state) \
            .select_for_display()

    def get_all_promoter_videos(self, promoter, age, gender, area_city, area_state):
        return self.get_active().exclude_featured().exclude_promoter(promoter) \
            .not_profiled(age, gender, area_city, area_state) \
            .select_for_display()

    def get_featured_everyone_videos(self):
        return self.get_featured().everyone().select_for_display()

    def get_non_featured_everyone_videos(self):
        return self.get_active().exclude_featured().everyone().select_for_display()

    def get_featured_non_everyone_videos(self):
        return self.get_featured().not_everyone().select_for_display()

    def get_non_featured_non_everyone_videos(self):
        return self.get_active().exclude_featured().not_everyone().select_for_display()

    def get_videos_for_authentication(self):
        return self.get_queryset().filter(videostate__active_head=True, videostate__current__in=['TC', 'ED']).order_by(
            '-create_time')

    def get_payment_due_videos(self):
        return self.get_queryset().filter(videostate__active_head=True, videostate__current__in=['IF', 'EP'])

    def get_file_upload_due_videos(self):
        return self.get_queryset().filter(videostate__active_head=True, videostate__current='PA')

    def get_in_auth_process_videos(self):
        return self.get_queryset().filter(videostate__active_head=True,
                                          videostate__current__in=['VU', 'VC', 'GC', 'TC', 'ED'])

    def get_edit_videos(self):
        return self.get_queryset().filter(videostate__active_head=True, videostate__current__in=['EC', 'EA'])

    def get_completed_videos(self):
        return self.get_queryset().filter(videostate__active_head=True, videostate__current='CO')

    def get_error_videos(self):
        return self.get_queryset().filter(videostate__active_head=True, videostate__current='EG')


class VideoCategoryManager(models.Manager):
    def get_queryset(self):
        return super(VideoCategoryManager, self).get_queryset()

    def get_promoter_categories(self, promoter):
        return self.get_queryset().filter(profiling__promoter_id=promoter).order_by('-profiling__score')


class VideoCategory(models.Model):
    category_name = models.CharField(max_length=20)
    create_time = models.DateTimeField(auto_now_add=True)

    objects = VideoCategoryManager()

    def __unicode__(self):
        return self.category_name


class Video(models.Model):
    client_id = models.ForeignKey('client.ClientProfile')
    max_coins = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=200)
    featured = models.BooleanField(default=False)
    active = models.BooleanField(default=False)
    publisher = models.CharField(max_length=50, blank=True, null=True)
    category = models.ManyToManyField(VideoCategory)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    slug = models.SlugField(unique=True, max_length=100)
    parent_video = models.ForeignKey('self', blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    objects = VideoManager()

    def video_index_details(self):
        categories = self.category.all()
        return self.video_url, self.max_coins, self.name, self.image, self.publisher, categories

    def __unicode__(self):
        return self.name

    def get_category(self):
        return "\n".join([p.category_name for p in self.category.all()])

    def save(self, *args, **kwargs):
        if not self.id:
            # Newly created object, so set slug
            slug_string = '{0} {1}'.format(self.name, datetime.datetime.now())
            self.slug = slugify(slug_string)

        super(Video, self).save(*args, **kwargs)

    def increment_views_anonymous_viewers(self):
        self.videoinsights.anonymous_viewers += 1
        self.videoinsights.save()

    def increment_views_promoter(self):
        self.videoinsights.promoters += 1
        self.videoinsights.save()

    def increment_insights_redirection_click(self):
        self.videoinsights.redirection_click += 1
        self.videoinsights.save()

    def increment_insights_backlinks(self):
        self.videoinsights.backlinks += 1
        self.videoinsights.save()

    def increment_video_account_expenditure(self, coins):
        self.videoaccount.expenditure_coins += coins
        self.videoaccount.save()

    def set_video_inactive(self):
        previous_state = self.get_previous_state()
        self.create_state(previous_state, 'CO')
        self.active = False
        self.save()
        VideoCompletionLog.objects.create(video_id=self)

    def get_child_videos(self):
        return self.video_set.all()

    def get_previous_state(self):
        return self.videostate_set.get(active_head=True)

    def create_state(self, previous_state, current, error_meta=None, active_head=True):
        if previous_state:
            previous_state.set_previous_state_inactive()
        video_state = VideoState(video_id=self, previous=previous_state, current=current, error_meta=error_meta,
                                 active_head=active_head)
        video_state.save()


class VideoInfo(models.Model):
    video_id = models.OneToOneField(Video)
    desc = models.TextField(blank=True, null=True)
    banner_landing_page = models.URLField(blank=True, null=True)
    banner_landing_page_image = models.ImageField(upload_to=get_banner_file_path, null=True, blank=True)
    product_desc = models.URLField(blank=True, null=True)
    buy_product = models.URLField(blank=True, null=True)
    update_time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.video_id.name


class VideoProfile(models.Model):
    video_id = models.OneToOneField(Video)
    age = IntegerRangeField(default=(0, 150))
    GENDER = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('A', 'All')
    )
    gender = models.CharField(max_length=1, choices=GENDER, default='A')
    city = models.CharField(max_length=20, default='A')
    state = models.ManyToManyField('cities_light.Region', blank=True)
    update_time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.video_id.name

    def get_state(self):
        return "\n".join([p.name_ascii for p in self.state.all()])


class VideoAccount(models.Model):
    video_id = models.OneToOneField(Video)
    graph_id = models.OneToOneField('graph.Graph', null=True)
    expenditure_coins = models.PositiveIntegerField(default=0)
    max_viewership = models.PositiveIntegerField(default=0)
    video_cost = models.PositiveIntegerField()
    update_time = models.DateTimeField(auto_now=True)


class VideoInsights(models.Model):
    video_id = models.OneToOneField(Video)
    anonymous_viewers = models.PositiveIntegerField(default=0)
    promoters = models.PositiveIntegerField(default=0)
    redirection_click = models.PositiveIntegerField(default=0)
    backlinks = models.PositiveIntegerField(default=0)
    update_time = models.DateTimeField(auto_now=True)

    def total_views(self):
        return self.anonymous_viewers + self.promoters

    def __unicode__(self):
        return self.video_id.name


class VideoFile(models.Model):  # Avoid saving in transaction.atomic()
    video_id = models.OneToOneField(Video)
    video_file_orig = models.FileField(upload_to=get_video_file_path)
    thumbnail_image = models.ImageField(upload_to=get_thumbnail_file_path, null=True, blank=True)
    video_file_mp4 = models.FileField(null=True)
    video_file_webm = models.FileField(null=True)
    video_duration = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=6)
    update_time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.video_id.name

    # def save(self, *args, **kwargs):
    #     in_signal = kwargs.pop('InSignal', False)
    #     super(VideoFile, self).save(*args, **kwargs)
    #     if not in_signal:



class VideoState(models.Model):
    video_id = models.ForeignKey(Video)
    STATE_CHOICES = (
        ('IF', 'Info Filled'),
        ('EP', 'Pay Error'),
        ('PA', 'Paid'),
        ('VU', 'Uploaded'),
        ('VC', 'Video Converted'),
        ('EC', 'Video Convert Error'),
        ('GC', 'Graph Created'),
        ('EG', 'Graph Error'),
        ('TC', 'Tasks Completed'),
        ('EA', 'Authorization Error'),
        ('AA', 'Authorize and Activate'),
        ('ED', 'Edited'),
        ('CO', 'Completed'),
        ('ES', 'Security Error'),
        ('SS', 'Security Success'),
        ('FT', 'Force Terminated')
    )
    previous = models.OneToOneField('self', blank=True, null=True, verbose_name='Previous State')
    current = models.CharField(max_length=2, choices=STATE_CHOICES, verbose_name='Current State')
    error_meta = HStoreField(blank=True, null=True)
    active_head = models.BooleanField(default=False)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.get_current_display()

    def set_previous_state_inactive(self):
        self.active_head = False
        self.save()
