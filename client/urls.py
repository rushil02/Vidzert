from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^video/(?P<video_uuid>[^/]+)/$', views.insights, name='insights'),
    url(r'^videos/$', views.all_videos, name='all_videos'),
    url(r'^surveys/$', views.all_surveys, name='all_surveys'),
    url(r'^profile/$', views.client_profile_view, name='profile'),
    url(r'^profile/edit/', views.update_client_profile, name='update_profile'),
    url(r'^upload/', views.upload, name='upload'),
    url(r'^revise/(?P<video_uuid>[^/]+)/$', views.revise, name='revise'),
    url(r'^survey/$', views.client_survey_home, name='client_survey_home'),
    url(r'^create_survey/$', views.create_survey, name='create_survey'),
    url(r'^create_survey/(?P<survey_uuid>[^/]+)/$', views.create_question_set, name='create_question_set'),
    url(r'^create_survey/(?P<survey_uuid>[^/]+)/(?P<question_set_id>[0-9]+)/$', views.create_question,
        name='create_question'),
    url(r'^del$', views.delete_client, name='deactivate_client'),
    url(r'^upload_file/(?P<video_uuid>[^/]+)/$', views.upload_video_file, name='upload_file'),
    url(r'^payment/', include('client_transaction.urls', namespace='transaction')),
    url(r'^revise_survey/(?P<survey_uuid>[^/]+)/$', views.revise_survey, name='revise_survey'),
    url(r'^edit_video/(?P<video_uuid>[^/]+)/$', views.edit_handler, name='edit_video'),
    url(r'^activate_survey/(?P<survey_uuid>[^/]+)/$', views.survey_activate_request, name='survey_activate_request'),
    url(r'^edit_survey/(?P<survey_uuid>[^/]+)/$', views.edit_survey_handler, name='edit_survey'),
]
