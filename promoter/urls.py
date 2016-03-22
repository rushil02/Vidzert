__author__ = 'Rushil'

from django.conf.urls import url, include

from .import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^watch/(?P<video_uuid>[^/]+)/$', views.promoter_video_watch, name='promoter_watch'),
    url(r'^watched/', views.watched, name='watched'),
    url(r'^filled/', views.filled, name='filled'),
    url(r'^redirect/', views.redirection, name='redirect'),
    url(r'^profile/$', views.promoter_account_view, name='account'),
    url(r'^profile/edit/', views.update_profile, name='update_profile'),
    url(r'^viewed/', views.video_viewed, name='viewed'),
    url(r'^buy_perk/', views.buy_perk, name='buy_perk'),
    url(r'^abort/$', views.promoter_video_abort, name='promoter_abort'),
    url(r'^survey/$', views.survey_home_page, name='survey_home_page'),
    url(r'^fill_survey/(?P<survey_uuid>[^/]+)/$', views.fill_survey_v2, name='fill_survey'),
    url(r'^survey/completed/', views.survey_complete, name='survey_complete'),
    url(r'^redeem_coins/', include('promoter_transaction.urls', namespace='transaction')),
    url(r'^survey/back/', views.back_questionset, name='back_questionset'),
    url(r'^del/$', views.delete_promoter, name='deactivate_promoter'),
    url(r'^advance_notification/$', views.apply_adv_notification, name='apply_adv_notification'),
]