from django.contrib import admin
from .models import *

# Register your models here.


class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ('error_code', 'error_type', 'error_meta', 'timestamp')

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

    search_fields = ('error_type', 'error_meta')
    list_filter = ('error_code', 'error_type')
    date_hierarchy = 'timestamp'


class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('actor', 'actor_ip', 'action_type', 'act_meta', 'timestamp')

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

    search_fields = ('actor', 'actor_ip', 'action_type', 'act_meta',)
    list_filter = ('action_type',)
    date_hierarchy = 'timestamp'


admin.site.register(ErrorLog, ErrorLogAdmin)
admin.site.register(ActivityLog, ActivityLogAdmin)
