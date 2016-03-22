from django.conf.urls import url
from .import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^register_staff/', views.staff_registration, name='staff_register'),
]
