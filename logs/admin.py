from django.contrib import admin
from .models import *

# Register your models here.


class VideoPromoterLogAdmin(admin.ModelAdmin):
    list_display = ('video_id', 'promoter_id', 'ip', 'share_url', 'coins', 'position', 'device_type', 'create_time')

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

    search_fields = ('video_id__name', 'promoter_id__promoter_id__email')
    list_filter = ('device_type',)
    date_hierarchy = 'create_time'


class VideoUnsubscribedLogAdmin(admin.ModelAdmin):
    list_display = ('video_id', 'promoter_id', 'ip', 'position', 'device_type', 'duration', 'ad_clicked', 'create_time')

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

    search_fields = ('video_id__name', 'promoter_id__promoter_id__email')
    list_filter = ('device_type',)
    date_hierarchy = 'create_time'


class PerkTransactionLogAdmin(admin.ModelAdmin):
    list_display = ('ref_no', 'promoter_id', 'perk_id', 'eggs', 'transaction_time')

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

    search_fields = ('ref_no', 'promoter_id__promoter_id__email')
    list_filter = ('perk_id',)
    date_hierarchy = 'transaction_time'


class GrayListAdmin(admin.ModelAdmin):
    list_display = ('ip', 'user_id', 'create_time')

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

    search_fields = ('ip', 'user_id__email')
    date_hierarchy = 'create_time'


class BlackListAdmin(admin.ModelAdmin):
    list_display = ('ip', 'user_id', 'create_time')

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

    search_fields = ('ip', 'user_id__email')
    date_hierarchy = 'create_time'


class DurationWatchedLogAdmin(admin.ModelAdmin):
    list_display = ('video_id', 'promoter_id', 'ip', 'duration', 'ad_clicked', 'create_time')

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

    search_fields = ('video_id__name', 'promoter_id__promoter_id__email', 'ip')
    list_filter = ('ad_clicked',)
    date_hierarchy = 'create_time'


class VideoPromoterReplayLogAdmin(admin.ModelAdmin):
    list_display = ('video_id', 'promoter_id', 'ip', 'device_type', 'create_time')

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

    search_fields = ('video_id__name', 'promoter_id__promoter_id__email', 'ip')
    list_filter = ('device_type',)
    date_hierarchy = 'create_time'


class VideoPromoterPerkLogAdmin(admin.ModelAdmin):
    list_display = ('video_id', 'promoter_id', 'perk_id', 'quantity', 'create_time')

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

    search_fields = ('video_id__name', 'promoter_id__promoter_id__email',)
    list_filter = ('perk_id',)
    date_hierarchy = 'create_time'


class SurveyPromoterLogAdmin(admin.ModelAdmin):
    list_display = ('survey_id', 'promoter_id', 'ip', 'coins', 'position', 'device_type', 'create_time')

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

    search_fields = ('survey_id__title', 'promoter_id__promoter_id__email')
    list_filter = ('device_type',)
    date_hierarchy = 'create_time'


admin.site.register(VideoPromoterLog, VideoPromoterLogAdmin)
admin.site.register(VideoUnsubscribedLog, VideoUnsubscribedLogAdmin)
admin.site.register(PerkTransactionLog, PerkTransactionLogAdmin)
admin.site.register(GrayList, GrayListAdmin)
admin.site.register(BlackList, BlackListAdmin)
admin.site.register(DurationWatchedLog, DurationWatchedLogAdmin)
admin.site.register(VideoPromoterReplayLog, VideoPromoterReplayLogAdmin)
admin.site.register(VideoPromoterPerkLog, VideoPromoterPerkLogAdmin)
admin.site.register(SurveyPromoterLog, SurveyPromoterLogAdmin)
