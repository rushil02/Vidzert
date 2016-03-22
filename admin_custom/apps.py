from django.apps import AppConfig


class AdminCustomConfig(AppConfig):
    name = 'admin_custom'
    verbose_name = "Admin"

    def ready(self):
        import signals
