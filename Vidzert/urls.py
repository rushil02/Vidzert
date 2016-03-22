"""Vidzert URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from admin_custom.views_2 import set_browser_fingerprint
from django.views.generic import TemplateView


urlpatterns = [
    url(r'^db/', include(admin.site.urls)),
    url(r'^cl/', include('client.urls', namespace='client')),
    url(r'^', include('user_login.urls', namespace='user')),
    url(r'^pr/', include('promoter.urls', namespace='promoter')),
    url(r'^admin/', include('admin_custom.urls', namespace='admin')),
    url(r'^staff/', include('staff_custom.urls', namespace='staff')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^captcha/', include('captcha.urls')),
    url(r'^helpdesk/', include('helpdesk.urls', namespace='helpdesk')),
    url(r'^style_css/$', set_browser_fingerprint, name='set_browser_fingerprint'),

    # url(r'^video/', include('video.urls', namespace='video')),
    # url(r'^watch/', include('video.urls', namespace='video'))
]

urlpatterns += [
    url(r'^about/$', TemplateView.as_view(template_name="flatpages/about.html"), name="about"),
    url(r'^FAQ/$', TemplateView.as_view(template_name="flatpages/faq.html"), name="faq"),
    url(r'^terms/$', TemplateView.as_view(template_name="flatpages/tou.html"), name="tou"),
    url(r'^security/$', TemplateView.as_view(template_name="flatpages/security.html"), name="security"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = 'Vidzert'
admin.site.site_title = 'Vidzert Site Admin'
