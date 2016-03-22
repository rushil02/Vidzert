from django.contrib import admin
from .models import *

# Register your models here.


class PromoterTransactionLogAdmin(admin.ModelAdmin):
    list_display = ('ref_no', 'promoter_id', 'payment_type', 'coins', 'amount', 'TDS', 'create_time', 'update_time')

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            self.readonly_fields = ()
        else:
            self.readonly_fields = self.list_display
        return self.readonly_fields

    def get_list_display_links(self, request, list_display):
        if request.user.is_superuser:
            self.list_display_links = list(list_display)[:1]
        else:
            self.list_display_links = None
        return self.list_display_links

    date_hierarchy = 'create_time'
    list_filter = ('payment_type',)
    search_fields = ('promoter_id__promoter_id__email', 'ref_no')


class PromoterMoneyAccountAdmin(admin.ModelAdmin):
    list_display = ('promoter_id', 'total_money', 'total_voucher', 'total_paytm', 'total_neft', 'update_time')

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            self.readonly_fields = ()
        else:
            self.readonly_fields = self.list_display
        return self.readonly_fields

    def get_list_display_links(self, request, list_display):
        if request.user.is_superuser:
            self.list_display_links = list(list_display)[:1]
        else:
            self.list_display_links = None
        return self.list_display_links

    date_hierarchy = 'update_time'
    search_fields = ('promoter_id__promoter_id__email',)


admin.site.register(PromoterTransactionLog, PromoterTransactionLogAdmin)
admin.site.register(PromoterMoneyAccount, PromoterMoneyAccountAdmin)