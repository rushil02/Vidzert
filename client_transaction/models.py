from django.db import models
import uuid
from django.db.models import Sum

# Create your models here.


class ClientTransactionLogManager(models.Manager):
    def get_queryset(self):
        return super(ClientTransactionLogManager, self).get_queryset()

    def client_transaction_log_entry(self, invoice_number, client, video, amount):
        return self.get_queryset().create(invoice_number=invoice_number, client_id=client, video_id=video, amount=amount)

    def get_total_turnover(self):
        return self.get_queryset().all().aggregate(total_amount=Sum('amount'))


class ClientTransactionLog(models.Model):
    invoice_number = models.CharField(max_length=10, unique=True)
    client_id = models.ForeignKey('client.ClientProfile')
    video_id = models.ForeignKey('video.Video')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    rate_of_tax = models.DecimalField(max_digits=5, decimal_places=4, default=0.1236)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    transaction_time = models.DateTimeField(auto_now_add=True)

    objects = ClientTransactionLogManager()

    def __unicode__(self):
        return '%s' % self.invoice_number
