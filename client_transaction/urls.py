from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^success_v/(?P<video_uuid>[^/]+)/$', views.success_video, name='success_video'),
    url(r'^success_s/(?P<survey_uuid>[^/]+)/$', views.success_survey, name='success_survey'),
]
