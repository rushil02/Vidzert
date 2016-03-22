from django.contrib import admin
from .models import *

# Register your models here.


class PerksAdmin(admin.ModelAdmin):
    list_display = ('perk_id', 'name', 'cost', 'times_used', 'block', 'update_time', 'create_time')

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


admin.site.register(Perks, PerksAdmin)
