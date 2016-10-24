# coding: utf-8
from rest_framework import serializers
import models
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        write_only_fields = ('password',)

    def update(self, attrs, instance=None):
        user = super(UserSerializer, self).update(attrs, instance)
        user.set_password(attrs['password'])
        return user


class AuthGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AuthGroup

        fields = ('name',)


class AuthGroupPermissionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AuthGroupPermissions

        fields = ('group', 'permission')


class AuthPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AuthPermission

        fields = ('name', 'content_type', 'codename')


class AuthUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AuthUser

        fields = ('password', 'last_login', 'is_superuser', 'username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'date_joined')


class AuthUserGroupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AuthUserGroups

        fields = ('user', 'group')


class AuthUserUserPermissionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AuthUserUserPermissions

        fields = ('user', 'permission')


class AuthtokenTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AuthtokenToken

        fields = ('key', 'created', 'user')


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Cliente

        fields = ('id', 'nome', 'telefone', 'endereceo', 'numero', 'cidade', 'pais', 'marca_id')


class DashboardUserdashboardmoduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DashboardUserdashboardmodule

        fields = ('title', 'module', 'app_label', 'user', 'column', 'order', 'settings', 'children', 'collapsed')


class DjangoAdminLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DjangoAdminLog

        fields = ('action_time', 'object_id', 'object_repr', 'action_flag', 'change_message', 'content_type', 'user')


class DjangoContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DjangoContentType

        fields = ('app_label', 'model')


class DjangoMigrationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DjangoMigrations

        fields = ('app', 'name', 'applied')


class DjangoSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DjangoSession

        fields = ('session_key', 'session_data', 'expire_date')


class EstrelaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Estrela

        fields = ('id', 'estado', 'valor', 'status', 'estrelacol')


class JetBookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.JetBookmark

        fields = ('url', 'title', 'user', 'date_add')


class JetPinnedapplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.JetPinnedapplication

        fields = ('app_label', 'user', 'date_add')


class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Marca

        fields = ('id', 'nome', 'descricao', 'serie', 'created', 'email')


class Oauth2ProviderAccesstokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Oauth2ProviderAccesstoken

        fields = ('token', 'expires', 'scope', 'application', 'user')


class Oauth2ProviderApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Oauth2ProviderApplication

        fields = ('client_id', 'redirect_uris', 'client_type', 'authorization_grant_type', 'client_secret', 'name', 'user', 'skip_authorization')


class Oauth2ProviderGrantSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Oauth2ProviderGrant

        fields = ('code', 'expires', 'redirect_uri', 'scope', 'application', 'user')


class Oauth2ProviderRefreshtokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Oauth2ProviderRefreshtoken

        fields = ('token', 'access_token', 'application', 'user')

