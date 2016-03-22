from django.apps import AppConfig


class VideoConfig(AppConfig):
    name = 'video'
    verbose_name = "Video"

    def ready(self):
        from video import (signals, dispatcher)