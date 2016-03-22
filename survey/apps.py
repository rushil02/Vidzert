from django.apps import AppConfig


class SurveyConfig(AppConfig):
    name = 'survey'
    verbose_name = "Survey"

    def ready(self):
        import signals
