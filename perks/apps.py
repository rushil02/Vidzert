from django.apps import AppConfig


class PerksConfig(AppConfig):
    name = 'perks'
    verbose_name = "Perks"

    def ready(self):
        import signals
