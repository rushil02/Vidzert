from django.contrib import admin
from .models import *


# Register your models here.


class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('client_id', 'address', 'contact2', 'website', 'update_time', 'create_time')

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

    search_fields = ('client_id__email', 'address', 'website', 'contact2', 'client_id__name', 'client_id__mobile')
    date_hierarchy = 'create_time'


admin.site.register(ClientProfile, ClientProfileAdmin)
