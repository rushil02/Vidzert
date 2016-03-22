from django.contrib import admin
from models import *


# Register your models here.


class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'client_id', 'max_coins', 'active', 'get_category', 'create_time', 'update_time')

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

    list_filter = ('active', 'category__category_name',)
    date_hierarchy = 'create_time'
    search_fields = ('client_id__client_id__email', 'client_id__client_id__name', 'title',)


class SurveyInfoAdmin(admin.ModelAdmin):
    list_display = ('survey_id', 'desc', 'banner_landing_page',
                    'banner_landing_page_image', 'update_time')

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
    search_fields = ('survey_id__client_id__client_id__email', 'survey_id__client_id__client_id__name',
                     'survey_id__title',)


class SurveyProfileAdmin(admin.ModelAdmin):
    list_display = ('survey_id', 'age', 'gender', 'city', 'get_state', 'update_time')

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
    search_fields = ('survey_id__client_id__client_id__email', 'survey_id__client_id__client_id__name',
                     'survey_id__title',)


class SurveyAccountAdmin(admin.ModelAdmin):
    list_display = ('survey_id', 'expenditure_coins', 'max_fill', 'survey_cost', 'update_time')

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
    search_fields = ('survey_id__client_id__client_id__email', 'survey_id__client_id__client_id__name',
                     'survey_id__title',)


class SurveyInsightsAdmin(admin.ModelAdmin):
    list_display = ('survey_id', 'promoters', 'partial_promoters', 'redirection_click',
                    'total_fills', 'update_time')

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
    search_fields = ('survey_id__client_id__client_id__email', 'survey_id__client_id__client_id__name',
                     'survey_id__title',)


class QuestionSetAdmin(admin.ModelAdmin):
    list_display = ('survey_id', 'sort_id', 'heading', 'help_text',
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

    ordering = ('-update_time',)
    search_fields = ('survey_id__client_id__client_id__email', 'survey_id__client_id__client_id__name',
                     'survey_id__title',)


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_set_id', 'number', 'sort_id', 'text',
                    'question_type', 'extra_text', 'required', 'footer_text',
                    'create_time', 'update_time', 'choices')

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
    search_fields = (
        'question_set_id__survey_id__client_id__client_id__email',
        'question_set_id__survey_id__client_id__client_id__name',
        'question_set_id__survey_id__title',)


class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question_id', 'promoter_id', 'answer_text',
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

    ordering = ('-create_time',)
    search_fields = ('question_id__question_set_id__survey_id__client_id__client_id__email',
                     'question_id__question_set_id__survey_id__client_id__client_id__name',
                     'question_id__question_set_id__survey_id__title',)


admin.site.register(Survey, SurveyAdmin)
admin.site.register(SurveyInfo, SurveyInfoAdmin)
admin.site.register(SurveyProfile, SurveyProfileAdmin)
admin.site.register(SurveyAccount, SurveyAccountAdmin)
admin.site.register(SurveyInsights, SurveyInsightsAdmin)
admin.site.register(QuestionSet, QuestionSetAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(SurveyState)
