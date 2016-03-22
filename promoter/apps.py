from django.apps import AppConfig


class PromoterConfig(AppConfig):
    name = 'promoter'
    verbose_name = "Promoter"

    def ready(self):
        import signals
