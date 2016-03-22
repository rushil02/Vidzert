from django.contrib import admin
from .models import *

# Register your models here.


class PromoterProfileAdmin(admin.ModelAdmin):

    def get_list_display(self, request):
        if request.user.is_superuser:
            self.list_display = ('promoter_id', 'last_name', 'dob', 'gender', 'area_city',
                                 'area_state', 'PAN', 'update_time', 'create_time')
        else:
            self.list_display = ('promoter_id', 'last_name', 'dob', 'gender', 'area_city',
                                 'area_state', 'update_time', 'create_time')
        return self.list_display

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            self.readonly_fields = ()
        else:
            self.readonly_fields = ('promoter_id', 'last_name', 'dob', 'gender', 'area_city',
                                    'area_state', 'update_time', 'create_time')
        return self.readonly_fields

    def get_list_display_links(self, request, list_display):
        if request.user.is_superuser:
            self.list_display_links = list(list_display)[:1]
        else:
            self.list_display_links = None
        return self.list_display_links

    list_filter = ('gender', 'area_state')
    date_hierarchy = 'create_time'
    search_fields = ('PAN', 'promoter_id__email', 'promoter_id__name', 'promoter_id__mobile', 'area_city')


class PromoterAccountAdmin(admin.ModelAdmin):
    list_display = ('promoter_id', 'current_coins', 'current_eggs', 'total_coins', 'total_eggs',
                    'mail_notification_flag', 'get_promoter_perk', 'update_time')

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

    list_filter = ('mail_notification_flag', 'perks')
    ordering = ('promoter_id__promoter_id__email',)
    search_fields = ('promoter_id__promoter_id__email', 'promoter_id__promoter_id__mobile',
                     'promoter_id__promoter_id__name',)


class ProfilingAdmin(admin.ModelAdmin):
    list_display = ('promoter_id', 'category_id', 'backlinks',
                    'engagement', 'views', 'survey_fills', 'score', 'update_time')

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

    list_filter = ('category_id',)
    ordering = ('promoter_id__promoter_id__email',)
    search_fields = ('promoter_id__promoter_id__email', )


class PromoterPerksAdmin(admin.ModelAdmin):
    list_display = ('promoter_id', 'perk_id', 'quantity', 'update_time')

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

    list_filter = ('perk_id',)
    ordering = ('promoter_id__promoter_id__promoter_id__email',)
    search_fields = ('promoter_id__promoter_id__promoter_id__email', )


admin.site.register(PromoterProfile, PromoterProfileAdmin)
admin.site.register(PromoterAccount, PromoterAccountAdmin)
admin.site.register(Profiling, ProfilingAdmin)
admin.site.register(PromoterPerks, PromoterPerksAdmin)
