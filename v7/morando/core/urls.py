# coding: utf-8
from django.conf.urls import url, include
from rest_framework import routers
import views

router = routers.DefaultRouter()
router.register(r'users', views.UserView, 'list')
router.register(r'authgroups', views.AuthGroupView, 'list')
router.register(r'authgrouppermissionss', views.AuthGroupPermissionsView, 'list')
router.register(r'authpermissions', views.AuthPermissionView, 'list')
router.register(r'authusers', views.AuthUserView, 'list')
router.register(r'authusergroupss', views.AuthUserGroupsView, 'list')
router.register(r'authuseruserpermissionss', views.AuthUserUserPermissionsView, 'list')
router.register(r'authtokentokens', views.AuthtokenTokenView, 'list')
router.register(r'clientes', views.ClienteView, 'list')
router.register(r'dashboarduserdashboardmodules', views.DashboardUserdashboardmoduleView, 'list')
router.register(r'djangoadminlogs', views.DjangoAdminLogView, 'list')
router.register(r'djangocontenttypes', views.DjangoContentTypeView, 'list')
router.register(r'djangomigrationss', views.DjangoMigrationsView, 'list')
router.register(r'djangosessions', views.DjangoSessionView, 'list')
router.register(r'estrelas', views.EstrelaView, 'list')
router.register(r'jetbookmarks', views.JetBookmarkView, 'list')
router.register(r'jetpinnedapplications', views.JetPinnedapplicationView, 'list')
router.register(r'marcas', views.MarcaView, 'list')
router.register(r'oauth2provideraccesstokens', views.Oauth2ProviderAccesstokenView, 'list')
router.register(r'oauth2providerapplications', views.Oauth2ProviderApplicationView, 'list')
router.register(r'oauth2providergrants', views.Oauth2ProviderGrantView, 'list')
router.register(r'oauth2providerrefreshtokens', views.Oauth2ProviderRefreshtokenView, 'list')

urlpatterns = [
    url(r'^', include(router.urls)),
]
