from django.dispatch import receiver
from django.db.models.signals import post_save
from models import Survey, SurveyInsights


@receiver(post_save, sender=Survey)
def set_survey_insight(sender, **kwargs):
    if kwargs.get('created', True):
        survey = kwargs.get('instance')
        SurveyInsights.objects.create(survey_id=survey)
