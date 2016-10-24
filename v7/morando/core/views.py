# coding: utf-8
from rest_framework.filters import DjangoFilterBackend
from rest_framework import viewsets
from django.contrib.auth.models import User
import models
import serializers


class UserView(viewsets.ModelViewSet):
    serializer_class = serializers.UserSerializer
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['username', 'email']


class AuthGroupView(viewsets.ModelViewSet):
    serializer_class = serializers.AuthGroupSerializer
    queryset = models.AuthGroup.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['name']


class AuthGroupPermissionsView(viewsets.ModelViewSet):
    serializer_class = serializers.AuthGroupPermissionsSerializer
    queryset = models.AuthGroupPermissions.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['group', 'permission']


class AuthPermissionView(viewsets.ModelViewSet):
    serializer_class = serializers.AuthPermissionSerializer
    queryset = models.AuthPermission.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['name', 'content_type', 'codename']


class AuthUserView(viewsets.ModelViewSet):
    serializer_class = serializers.AuthUserSerializer
    queryset = models.AuthUser.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['password', 'last_login', 'is_superuser', 'username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'date_joined']


class AuthUserGroupsView(viewsets.ModelViewSet):
    serializer_class = serializers.AuthUserGroupsSerializer
    queryset = models.AuthUserGroups.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['user', 'group']


class AuthUserUserPermissionsView(viewsets.ModelViewSet):
    serializer_class = serializers.AuthUserUserPermissionsSerializer
    queryset = models.AuthUserUserPermissions.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['user', 'permission']


class AuthtokenTokenView(viewsets.ModelViewSet):
    serializer_class = serializers.AuthtokenTokenSerializer
    queryset = models.AuthtokenToken.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['key', 'created', 'user']


class ClienteView(viewsets.ModelViewSet):
    serializer_class = serializers.ClienteSerializer
    queryset = models.Cliente.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['id', 'nome', 'telefone', 'endereceo', 'numero', 'cidade', 'pais', 'marca_id']


class DashboardUserdashboardmoduleView(viewsets.ModelViewSet):
    serializer_class = serializers.DashboardUserdashboardmoduleSerializer
    queryset = models.DashboardUserdashboardmodule.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['title', 'module', 'app_label', 'user', 'column', 'order', 'settings', 'children', 'collapsed']


class DjangoAdminLogView(viewsets.ModelViewSet):
    serializer_class = serializers.DjangoAdminLogSerializer
    queryset = models.DjangoAdminLog.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['action_time', 'object_id', 'object_repr', 'action_flag', 'change_message', 'content_type', 'user']


class DjangoContentTypeView(viewsets.ModelViewSet):
    serializer_class = serializers.DjangoContentTypeSerializer
    queryset = models.DjangoContentType.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['app_label', 'model']


class DjangoMigrationsView(viewsets.ModelViewSet):
    serializer_class = serializers.DjangoMigrationsSerializer
    queryset = models.DjangoMigrations.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['app', 'name', 'applied']


class DjangoSessionView(viewsets.ModelViewSet):
    serializer_class = serializers.DjangoSessionSerializer
    queryset = models.DjangoSession.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['session_key', 'session_data', 'expire_date']


class EstrelaView(viewsets.ModelViewSet):
    serializer_class = serializers.EstrelaSerializer
    queryset = models.Estrela.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['id', 'estado', 'valor', 'status', 'estrelacol']


class JetBookmarkView(viewsets.ModelViewSet):
    serializer_class = serializers.JetBookmarkSerializer
    queryset = models.JetBookmark.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['url', 'title', 'user', 'date_add']


class JetPinnedapplicationView(viewsets.ModelViewSet):
    serializer_class = serializers.JetPinnedapplicationSerializer
    queryset = models.JetPinnedapplication.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['app_label', 'user', 'date_add']


class MarcaView(viewsets.ModelViewSet):
    serializer_class = serializers.MarcaSerializer
    queryset = models.Marca.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['id', 'nome', 'descricao', 'serie', 'created', 'email']


class Oauth2ProviderAccesstokenView(viewsets.ModelViewSet):
    serializer_class = serializers.Oauth2ProviderAccesstokenSerializer
    queryset = models.Oauth2ProviderAccesstoken.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['token', 'expires', 'scope', 'application', 'user']


class Oauth2ProviderApplicationView(viewsets.ModelViewSet):
    serializer_class = serializers.Oauth2ProviderApplicationSerializer
    queryset = models.Oauth2ProviderApplication.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['client_id', 'redirect_uris', 'client_type', 'authorization_grant_type', 'client_secret', 'name', 'user', 'skip_authorization']


class Oauth2ProviderGrantView(viewsets.ModelViewSet):
    serializer_class = serializers.Oauth2ProviderGrantSerializer
    queryset = models.Oauth2ProviderGrant.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['code', 'expires', 'redirect_uri', 'scope', 'application', 'user']


class Oauth2ProviderRefreshtokenView(viewsets.ModelViewSet):
    serializer_class = serializers.Oauth2ProviderRefreshtokenSerializer
    queryset = models.Oauth2ProviderRefreshtoken.objects.all()
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['token', 'access_token', 'application', 'user']
