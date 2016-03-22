from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import HStoreField


class StaffProfile(models.Model):
    staff_id = models.OneToOneField(settings.AUTH_USER_MODEL)
    last_name = models.CharField(max_length=30, null=True)
    dob = models.DateField(null=True)
    GENDER = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    gender = models.CharField(max_length=1, choices=GENDER, null=True)
    address = models.CharField(max_length=250, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)


class TransactionUpdateLogManager(models.Manager):
    def get_queryset(self):
        return super(TransactionUpdateLogManager, self).get_queryset()

    def create_transaction_update(self, transaction, staff, fields_updated):
        return self.get_queryset().create(transaction_id=transaction, staff_id=staff, fields_updated=fields_updated)


class TransactionUpdateLog(models.Model):
    transaction_id = models.ForeignKey('promoter_transaction.PromoterTransactionLog')
    staff_id = models.ForeignKey(StaffProfile)
    fields_updated = HStoreField()
    create_time = models.DateTimeField(auto_now_add=True)

    objects = TransactionUpdateLogManager()


class VideoAuthoriseLog(models.Model):
    video_id = models.ForeignKey('video.Video')
    staff_id = models.ForeignKey(StaffProfile)
    fields_updated = HStoreField()
    create_time = models.DateTimeField(auto_now_add=True)


class SurveyAuthoriseLog(models.Model):
    survey_id = models.ForeignKey('survey.Survey')
    staff_id = models.ForeignKey(StaffProfile)
    fields_updated = HStoreField()
    create_time = models.DateTimeField(auto_now_add=True)