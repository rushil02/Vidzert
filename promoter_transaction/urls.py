
__author__ = 'Pranav'


from django.conf.urls import url

from .import views

urlpatterns = [
    url(r'^prepaid/$', views.prepaid_recharge_view, name='prepaid'),
    url(r'^postpaid/$', views.postpaid_recharge_view, name='postpaid'),
    url(r'^paytm/$', views.paytm_transfer_view, name='paytm')
]
