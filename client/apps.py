from django.apps import AppConfig


class ClientConfig(AppConfig):
    name = 'client'
    verbose_name = "Client"

    def ready(self):
        import signals
