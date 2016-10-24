"""liberdade URL Configuration

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
from django.conf.urls import include, url
from django.contrib import admin
from rest_framework_swagger.views import get_swagger_view
from core.views import obtain_auth_token, password_reset
from django.contrib.auth.views import password_reset as pass_reset_django
from django.contrib.auth.views import password_reset_done as reset_done
from django.contrib.auth.views import password_reset_confirm as reset_confirm
from django.contrib.auth.views import password_reset_complete as reset_complete


urlpatterns = [
    url(r'^jet/', include('jet.urls', 'jet')),  # Django JET URLS
    url(r'^jet/dashboard/', include('jet.dashboard.urls', 'jet-dashboard')),  # Django JET dashboard URLS
    url(r'^admin/', include(admin.site.urls)),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^v1/', include('core.urls')),
    url(r'^v1/docs/', get_swagger_view(title='REST Project')),
    url(r'^v1/auth/', include('rest_framework_social_oauth2.urls')), # Social Login

    url(r'^v1/token-auth/', obtain_auth_token),

    url(r'^v1/password-reset/$', password_reset, {'post_reset_redirect' : '/accounts/password_reset/mailed/'}, name='password-reset'),

    # To use management credentials in web page and reset password
    url(r'^v1/accounts/password_reset/$', pass_reset_django, {'post_reset_redirect': '/accounts/password_reset/mailed/'}, name="password_reset"),
    url(r'^v1/accounts/password_reset/mailed/$', reset_done, name="password_reset_confirm"),
    url(r'^v1/accounts/password_reset/(?P<uidb64>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', reset_confirm,  {'post_reset_redirect' : '/accounts/password_reset/complete/'}, name="password_reset_confirm"),
    url(r'^v1/accounts/password_reset/complete/$', reset_complete),

    url(r'^v1/o/', include('oauth2_provider.urls', namespace='oauth2_provider')), #social Login
    url(r'^v1/rest-auth/', include('rest_auth.urls')), #default autentication

]
