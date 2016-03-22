__author__ = 'Pranav'

from django.conf.urls import url
from .import views


urlpatterns = [
    url(r'^$', views.submit_ticket, name='submit_ticket'),
    url(r'^view/(?P<ticket_uuid>[^/]+)/', views.show_ticket, name='show_ticket'),
    url(r'^check_ticket/', views.check_ticket, name='check_ticket'),
    url(r'^admin/$', views.staff_home, name='staff_home'),
    url(r'^admin/view/(?P<ticket_uuid>[^/]+)/', views.staff_ticket_view, name='staff_ticket_view'),

]