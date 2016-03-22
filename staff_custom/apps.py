from django.apps import AppConfig


class StaffConfig(AppConfig):
    name = 'staff_custom'
    verbose_name = "Staff"

    def ready(self):
        import signals
