from django.contrib import admin
from .models import *

# Register your models here.


class VideoCategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'create_time')

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


class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'client_id', 'max_coins',
                    'featured', 'active', 'publisher', 'slug', 'uuid',
                    'get_category', 'parent_video', 'create_time', 'update_time',)

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

    list_filter = ('active', 'category__category_name', 'featured',)
    date_hierarchy = 'create_time'
    search_fields = ('client_id__client_id__email', 'client_id__client_id__name', 'name', 'publisher', 'uuid')


class VideoInfoAdmin(admin.ModelAdmin):
    list_display = ('video_id', 'desc', 'banner_landing_page', 'product_desc',
                    'buy_product', 'banner_landing_page_image', 'update_time')

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

    ordering = ('-update_time',)
    search_fields = ('video_id__client_id__client_id__email', 'video_id__client_id__client_id__name',
                     'video_id__name', 'video_id__publisher',)


class VideoProfileAdmin(admin.ModelAdmin):
    list_display = ('video_id', 'age', 'gender', 'city', 'get_state', 'update_time')

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

    list_filter = ('gender',)
    ordering = ('-update_time',)
    search_fields = ('video_id__client_id__client_id__email', 'video_id__client_id__client_id__name',
                     'video_id__name', 'video_id__publisher',)


class VideoAccountAdmin(admin.ModelAdmin):
    list_display = ('video_id', 'expenditure_coins', 'max_viewership', 'video_cost', 'update_time')

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

    ordering = ('-update_time',)
    search_fields = ('video_id__client_id__client_id__email', 'video_id__client_id__client_id__name',
                     'video_id__name', 'video_id__publisher',)


class VideoInsightsAdmin(admin.ModelAdmin):
    list_display = ('video_id', 'anonymous_viewers', 'promoters', 'redirection_click', 'backlinks',
                    'total_views', 'update_time')

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

    ordering = ('-update_time',)
    search_fields = ('video_id__client_id__client_id__email', 'video_id__client_id__client_id__name',
                     'video_id__name', 'video_id__publisher',)


class VideoFileAdmin(admin.ModelAdmin):
    list_display = ('video_id', 'video_file_orig', 'thumbnail_image', 'video_file_mp4', 'video_file_webm',
                    'video_duration', 'update_time')

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

    ordering = ('-update_time',)
    search_fields = ('video_id__client_id__client_id__email', 'video_id__client_id__client_id__name',
                     'video_id__name', 'video_id__publisher',)


class VideoStateAdmin(admin.ModelAdmin):
    list_display = ('video_id', 'previous', 'current', 'error_meta', 'active_head', 'create_time', 'update_time')

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

    list_filter = ('current', 'active_head')
    ordering = ('-update_time',)
    search_fields = ('video_id__name', 'error_meta')

admin.site.register(VideoCategory, VideoCategoryAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(VideoInfo, VideoInfoAdmin)
admin.site.register(VideoProfile, VideoProfileAdmin)
admin.site.register(VideoAccount, VideoAccountAdmin)
admin.site.register(VideoInsights, VideoInsightsAdmin)
admin.site.register(VideoFile, VideoFileAdmin)
admin.site.register(VideoState, VideoStateAdmin)
