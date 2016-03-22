from django.db import models
import uuid

# Create your models here.


class PerksManager(models.Manager):
    def get_queryset(self):
        return super(PerksManager, self).get_queryset()

    def get_perk(self, perk_uuid):
        return self.get_queryset().get(uuid=perk_uuid)

    def get_perk_object(self, perk_id):
        return self.get_queryset().get(perk_id=perk_id)

    def get_buy_perks(self, account):
        return self.get_queryset().filter(cost__lte=account.current_eggs)


class Perks(models.Model):
    perk_id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=30)
    cost = models.PositiveIntegerField(default=0)
    times_used = models.PositiveIntegerField(default=0)
    BLOCK_CHOICES = (
        ('F', 'Pre-Perks (Former)'),
        ('L', 'Post-Perks (Latter)'),
        ('M', 'Mail Perks'),
        ('U', 'Unrelated Perks'),
    )
    block = models.CharField(max_length=1, choices=BLOCK_CHOICES)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    objects = PerksManager()

    def __unicode__(self):
        return self.name

    def increment_times_used(self, quantity=1):
        self.times_used += quantity
        self.save()
