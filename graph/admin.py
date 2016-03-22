from django.contrib import admin
from .models import *

# Register your models here.


class GraphAdmin(admin.ModelAdmin):
    list_display = ('id', 'graph_file', 'stats', 'create_time')
    # list_display_links = ('get_parent',)

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            self.readonly_fields = ('graph_model', 'graph_user', 'user_pos', 'stats')
        else:
            self.readonly_fields = ('graph_id', 'graph_model', 'graph_file', 'graph_user', 'user_pos', 'stats',
                                    'create_time')
        return self.readonly_fields

    def get_list_display_links(self, request, list_display):
        if request.user.is_superuser:
            self.list_display_links = list(list_display)[:1]
        else:
            self.list_display_links = None
        return self.list_display_links

    def get_queryset(self, request):
        qs = super(GraphAdmin, self).get_queryset(request)
        return qs.defer('graph_model', 'graph_user', 'user_pos')

    # def get_parent(self, obj):
    #     if obj.videoaccount.video_id:
    #         print obj.videoaccount.video_id
    #         return obj.videoaccount.video_id
    #     else:
    #         return obj.surveyaccount.survey_id

    search_fields = ('graph_id__name',)  # FIXME: THE fuck is this?
    date_hierarchy = 'create_time'


class GraphCreationMetaAdmin(admin.ModelAdmin):
    list_display = ('graph_type', 'graph_meta', 'graph_win_model', 'active', 'create_time')

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            self.readonly_fields = ()
        else:
            self.readonly_fields = ('graph_type', 'graph_meta', 'graph_win_model',
                                    'active', 'create_time')
        return self.readonly_fields

    def get_list_display_links(self, request, list_display):
        if request.user.is_superuser:
            self.list_display_links = list(list_display)[:1]
        else:
            self.list_display_links = None
        return self.list_display_links

    list_filter = ('graph_type', 'active')
    search_fields = ('graph_meta',)
    date_hierarchy = 'create_time'

admin.site.register(Graph, GraphAdmin)
admin.site.register(GraphCreationMeta, GraphCreationMetaAdmin)
