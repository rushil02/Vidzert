__author__ = 'Rushil'

from django.apps import AppConfig


class GraphConfig(AppConfig):
    name = 'graph'
    verbose_name = "Graph"

    def ready(self):
        from . import (
            signals, dispatcher
        )
