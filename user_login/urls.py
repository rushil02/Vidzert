from django.conf.urls import url
from views import views_1, views_2, views_3, views_4, views_5


urlpatterns = [
    url(r'^$', views_1.main, name='user_type'),
    url(r'^login/$', views_1.user_login, name='login_seperate'),
    url(r'^logout/$', views_1.logout_view, name='logout'),
    url(r'^redirect/$', views_2.redirection, name='redirect'),
    url(r'^viewed/$', views_2.viewed, name='viewed'),
    url(r'^watch/(?P<slug>[^/]+)/$', views_2.anonymous_video_watch, name='anonymous_watch'),
    url(r'^watch/(?P<slug>[^/]+)/(?P<promoter_uuid>[^/]+)/$', views_2.anonymous_video_watch, name='backlink_watch'),
    url(r'^advertise/$', views_1.client_registration, name='client_registration'),
    url(r'^sign_up/$', views_1.sign_up, name='sign_up_seperate'),
    url(r'^top_earners/$', views_1.top_earners, name='top_earners'),

    url(r'^verify/(?P<token>[\w:-]+)$', views_5.verify_email, name='verify_email'),

    url(r'^recover/(?P<signature>.+)/$', views_4.RecoverDone.as_view(),
        name='password_reset_sent'),
    url(r'^recover/$', views_4.Recover.as_view(), name='password_reset_recover'),
    url(r'^reset/done/$', views_4.ResetDone.as_view(), name='password_reset_done'),
    url(r'^reset/(?P<token>[\w:-]+)/$', views_4.Reset.as_view(),
        name='password_reset_reset'),
    url(r'^login_c/$', views_1.user_login_captcha, name='login_secure'),
    url(r'^sign_up_c/$', views_1.sign_up_captcha, name='sign_up_secure'),

    url(r'^at_1/$', views_3.at_10_sec, name='at_10_seconds'),
    url(r'^at_3/$', views_3.at_30_sec, name='at_30_seconds'),
    url(r'^at_eov/$', views_3.eov_handler, name='at_end_of_video'),
    url(r'^at_ab/$', views_3.abort_handler, name='at_abort'),




]
