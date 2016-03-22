from django.contrib import admin
from models import StaffProfile, TransactionUpdateLog, VideoAuthoriseLog, SurveyAuthoriseLog

# Register your models here.


class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('staff_id', 'last_name', 'dob', 'gender', 'address',
                    'create_time', 'update_time')

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

    list_filter = ('gender', )
    date_hierarchy = 'create_time'
    search_fields = ('staff_id__email', 'staff_id__name', 'last_name', 'address', 'staff_id__mobile')


class TransactionUpdateLogAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'staff_id', 'fields_updated', 'create_time')

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


class VideoAuthoriseLogAdmin(admin.ModelAdmin):
    list_display = ('video_id', 'staff_id', 'fields_updated', 'create_time')

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


class SurveyAuthoriseLogAdmin(admin.ModelAdmin):
    list_display = ('survey_id', 'staff_id', 'fields_updated', 'create_time')

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


admin.site.register(StaffProfile, StaffProfileAdmin)
admin.site.register(TransactionUpdateLog, TransactionUpdateLogAdmin)
admin.site.register(VideoAuthoriseLog, VideoAuthoriseLogAdmin)
admin.site.register(SurveyAuthoriseLog, SurveyAuthoriseLogAdmin)
