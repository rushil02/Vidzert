from django.db import models
import uuid
from django.contrib.postgres.fields import HStoreField
from django.db.models import Sum

# Create your models here.


class PromoterTransactionLogManager(models.Manager):
    def get_queryset(self):
        return super(PromoterTransactionLogManager, self).get_queryset()

    def get_total_expense(self):
        return self.get_queryset().all().aggregate(total_amount=Sum('amount'))

    def get_paytm_transactions(self):
        return self.get_queryset().filter(payment_type='P').order_by('paid')

    def get_transaction(self, transaction_uuid):
        return self.get_queryset().get(uuid=transaction_uuid)


class PromoterTransactionLog(models.Model):
    ref_no = models.CharField(max_length=16, unique=True)
    promoter_id = models.ForeignKey('promoter.PromoterProfile')
    PAYMENT = (
        ('A', 'Voucher'),
        ('B', 'RTGS'),
        ('R', 'Recharge'),
        ('P', 'PayTM'),
    )
    payment_type = models.CharField(max_length=1, choices=PAYMENT, blank=True)
    coins = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    TDS = models.DecimalField(max_digits=15, decimal_places=2)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    extra = HStoreField(null=True, blank=True)
    paid = models.BooleanField()
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    objects = PromoterTransactionLogManager()


class PromoterMoneyAccount(models.Model):
    promoter_id = models.ForeignKey('promoter.PromoterProfile')
    total_money = models.DecimalField(max_digits=15, decimal_places=2)
    total_voucher = models.DecimalField(max_digits=15, decimal_places=2)
    total_paytm = models.DecimalField(max_digits=15, decimal_places=2)
    total_neft = models.DecimalField(max_digits=15, decimal_places=2)
    update_time = models.DateTimeField(auto_now=True)
