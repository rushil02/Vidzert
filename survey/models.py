from django.contrib.postgres.fields import HStoreField
from django.db import models
import uuid
from django.contrib.postgres.fields import IntegerRangeField
from django.db.models import Q
from admin_custom.models import SurveyCompletionLog
from django.contrib.postgres.fields import ArrayField


# Create your models here.


class SurveyQuerySet(models.query.QuerySet):
    def active(self):
        return self.filter(active=True)

    def get_from_uuid(self, survey_uuid):
        return self.get(uuid=survey_uuid)

    def exclude_promoter(self, promoter):
        return self.exclude(surveypromoterlog__promoter_id=promoter)

    def profiled(self, age, gender, area_city, area_state):
        return self.filter(Q(surveyprofile__age__contains=age),
                           Q(surveyprofile__gender=gender) | Q(surveyprofile__gender='A'),
                           Q(surveyprofile__state=area_state) | Q(surveyprofile__state=None))

    def exclude_categories(self, promoter_categories):
        return self.filter(~Q(category__in=promoter_categories))

    def include_categories(self, promoter_categories):
        return self.filter(category__in=promoter_categories)


class SurveyManager(models.Manager):
    def get_queryset(self):
        return SurveyQuerySet(self.model, using=self._db)

    def get_active(self):
        return self.get_queryset().active()

    def get_survey(self, survey_uuid):
        return self.get_queryset().get_from_uuid(survey_uuid)

    def get_all_profiled_surveys(self, promoter, promoter_categories, age, gender, area_city, area_state):
        return self.get_queryset().active().exclude_promoter(promoter).exclude_categories(promoter_categories).profiled(
            age, gender, area_city, area_state).order_by('update_time')

    def get_category_profiled_surveys(self, promoter, promoter_categories, age, gender, area_city, area_state):
        return self.get_queryset().active().exclude_promoter(promoter).include_categories(promoter_categories).profiled(
            age, gender, area_city, area_state).order_by('update_time')

    def get_surveys_for_authentication(self):
        return self.get_queryset().filter(surveystate__active_head=True,
                                          surveystate__current__in=['TC', 'ED']).order_by('-create_time')


class Survey(models.Model):
    client_id = models.ForeignKey('client.ClientProfile')
    max_coins = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=False)
    title = models.CharField(max_length=200)
    category = models.ManyToManyField('video.VideoCategory')
    parent_survey = models.ForeignKey('self', blank=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    check_flag = models.BooleanField(default=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    objects = SurveyManager()

    def __unicode__(self):
        return self.title

    def get_category(self):
        return "\n".join([p.category_name for p in self.category.all()])

    def increment_fill_promoter(self):
        self.surveyinsights.promoters += 1
        self.surveyinsights.save()

    def increment_survey_account_expenditure(self, coins):
        self.surveyaccount.expenditure_coins += coins
        self.surveyaccount.save()

    def set_survey_inactive(self):
        previous_state = self.get_previous_state()
        self.create_state(previous_state, 'CO')
        self.active = False
        self.save()
        SurveyCompletionLog.objects.create(survey_id=self)

    def get_previous_state(self):
        return self.surveystate_set.get(active_head=True)

    def create_state(self, previous_state, current, error_meta=None, active_head=True):
        if previous_state:
            previous_state.set_previous_state_inactive()
        survey_state = SurveyState(survey_id=self, previous=previous_state, current=current, error_meta=error_meta,
                                   active_head=active_head)
        survey_state.save()


class SurveyInfo(models.Model):
    survey_id = models.OneToOneField(Survey)
    desc = models.TextField(blank=True, null=True)
    banner_landing_page = models.URLField(blank=True, null=True)
    banner_landing_page_image = models.ImageField(upload_to='Survey/%Y/%m/%d/Images', null=True, blank=True)
    update_time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.survey_id.title


class SurveyProfile(models.Model):
    survey_id = models.OneToOneField(Survey)
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
        return self.survey_id.name

    def get_state(self):
        return "\n".join([p.name_ascii for p in self.state.all()])


class SurveyAccount(models.Model):  # Avoid saving in transaction.atomic()
    survey_id = models.OneToOneField(Survey)
    expenditure_coins = models.PositiveIntegerField(default=0)
    graph_id = models.OneToOneField('graph.Graph', null=True)
    max_fill = models.PositiveIntegerField(default=0)
    survey_cost = models.PositiveIntegerField()
    update_time = models.DateTimeField(auto_now=True)

    # def save(self, *args, **kwargs):
    #     in_signal = kwargs.pop('InSignal', False)
    #     force_create = kwargs.pop('force_create', False)
    #     super(SurveyAccount, self).save(*args, **kwargs)
    #     if not in_signal:
    #         create_graph.send(sender=self.__class__, force_create=force_create, instance=self)


class SurveyInsights(models.Model):
    survey_id = models.OneToOneField(Survey)
    promoters = models.PositiveIntegerField(default=0)
    partial_promoters = models.PositiveIntegerField(default=0)
    redirection_click = models.PositiveIntegerField(default=0)
    update_time = models.DateTimeField(auto_now=True)

    def total_fills(self):
        return self.promoters

    def __unicode__(self):
        return self.survey_id.title


class QuestionSet(models.Model):
    survey_id = models.ForeignKey(Survey)
    sort_id = models.PositiveIntegerField(default=1)
    heading = models.CharField(max_length=64)
    help_text = models.TextField(blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.heading


class Question(models.Model):
    question_set_id = models.ForeignKey(QuestionSet)
    number = models.CharField(max_length=8, blank=True, null=True)
    sort_id = models.PositiveIntegerField(default=1)
    text = models.TextField()
    QUESTION_TYPE = (
        ('CH1', 'Choice - Single'),
        ('CH2', 'Choice - Single + Comment'),
        ('CH3', 'Open'),
        ('CH4', 'Choice - Multiple'),
        ('CH6', 'Choice - Multiple + Comment'),
        ('CH7', 'Number')
    )
    question_type = models.CharField(max_length=3, choices=QUESTION_TYPE)
    extra_text = models.CharField(max_length=255, blank=True, null=True)
    required = models.BooleanField(default=False)
    footer_text = models.CharField(max_length=255, blank=True, null=True)
    choices = ArrayField(models.CharField(max_length=64), null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.question_set_id.survey_id.title


class Answer(models.Model):
    question_id = models.ForeignKey(Question)
    promoter_id = models.ForeignKey('promoter.PromoterProfile')
    answer_text = models.TextField()
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('question_id', 'promoter_id')


class SurveyState(models.Model):
    survey_id = models.ForeignKey(Survey)
    STATE_CHOICES = (
        ('IF', 'Info Filled'),
        ('EP', 'Pay Error'),
        ('PA', 'Paid'),
        ('SF', 'Survey Filled'),  # TODO: Graph creation signal after filled
        ('GC', 'Graph Created'),
        ('EG', 'Graph Error'),
        ('TC', 'Tasks Completed'),
        ('EA', 'Authorization Error'),
        ('AA', 'Authorize and Activate'),
        ('ED', 'Edited'),
        ('CO', 'Completed'),
        ('ES', 'Security Error'),
        ('SS', 'Security Success'),
    )
    previous = models.OneToOneField('self', blank=True, null=True)
    current = models.CharField(max_length=2, choices=STATE_CHOICES)
    error_meta = HStoreField(blank=True, null=True)
    active_head = models.BooleanField(default=False)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.survey_id.title + " " + self.current

    def set_previous_state_inactive(self):
        self.active_head = False
        self.save()
