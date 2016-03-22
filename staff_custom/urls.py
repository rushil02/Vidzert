from django.conf.urls import url
from .import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^paytm_recharge_home/', views.paytm_recharge_home, name='paytm_recharge_home'),
    url(r'^paytm_toggle_paid/(?P<transaction_uuid>[^/]+)/', views.paytm_recharge_paid, name='paytm_recharge_paid'),
    url(r'^video_authentication_home/', views.video_authentication_home, name='video_authentication_home'),
    url(r'^watch/(?P<video_uuid>[^/]+)/', views.staff_video_watch, name='staff_video_watch'),
    url(r'^authorise_video/(?P<video_uuid>[^/]+)/', views.authorise_activate_video, name='authorise_activate_video'),
    url(r'survey_authentication_home/', views.survey_authentication_home, name='survey_authentication_home'),
    url(r'^authorise_survey/(?P<survey_uuid>[^/]+)/', views.authorise_activate_survey,
        name='authorise_activate_survey'),
    url(r'^display_survey/(?P<survey_uuid>[^/]+)/', views.display_survey, name='authorise_activate_survey'),
    url(r'^del$', views.delete_staff_user, name='deactivate_staff_account'),
    url(r'^reject_video/(?P<video_uuid>[^/]+)/', views.reject_video, name='reject_video'),
    url(r'^reject_survey/(?P<survey_uuid>[^/]+)/', views.reject_survey, name='reject_survey'),
]
