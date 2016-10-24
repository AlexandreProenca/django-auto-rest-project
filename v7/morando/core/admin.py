# coding: utf-8
from django.contrib import admin
import models


class AuthGroup(admin.ModelAdmin):
    list_display = ['name']


class AuthGroupPermissions(admin.ModelAdmin):
    list_display = ['group', 'permission']


class AuthPermission(admin.ModelAdmin):
    list_display = ['name', 'content_type', 'codename']


class AuthUser(admin.ModelAdmin):
    list_display = ['password', 'last_login', 'is_superuser', 'username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'date_joined']


class AuthUserGroups(admin.ModelAdmin):
    list_display = ['user', 'group']


class AuthUserUserPermissions(admin.ModelAdmin):
    list_display = ['user', 'permission']


class AuthtokenToken(admin.ModelAdmin):
    list_display = ['key', 'created', 'user']


class Cliente(admin.ModelAdmin):
    list_display = ['id', 'nome', 'telefone', 'endereceo', 'numero', 'cidade', 'pais', 'marca_id']


class DashboardUserdashboardmodule(admin.ModelAdmin):
    list_display = ['title', 'module', 'app_label', 'user', 'column', 'order', 'settings', 'children', 'collapsed']


class DjangoAdminLog(admin.ModelAdmin):
    list_display = ['action_time', 'object_id', 'object_repr', 'action_flag', 'change_message', 'content_type', 'user']


class DjangoContentType(admin.ModelAdmin):
    list_display = ['app_label', 'model']


class DjangoMigrations(admin.ModelAdmin):
    list_display = ['app', 'name', 'applied']


class DjangoSession(admin.ModelAdmin):
    list_display = ['session_key', 'session_data', 'expire_date']


class Estrela(admin.ModelAdmin):
    list_display = ['id', 'estado', 'valor', 'status', 'estrelacol']


class JetBookmark(admin.ModelAdmin):
    list_display = ['url', 'title', 'user', 'date_add']


class JetPinnedapplication(admin.ModelAdmin):
    list_display = ['app_label', 'user', 'date_add']


class Marca(admin.ModelAdmin):
    list_display = ['id', 'nome', 'descricao', 'serie', 'created', 'email']


class Oauth2ProviderAccesstoken(admin.ModelAdmin):
    list_display = ['token', 'expires', 'scope', 'application', 'user']


class Oauth2ProviderApplication(admin.ModelAdmin):
    list_display = ['client_id', 'redirect_uris', 'client_type', 'authorization_grant_type', 'client_secret', 'name', 'user', 'skip_authorization']


class Oauth2ProviderGrant(admin.ModelAdmin):
    list_display = ['code', 'expires', 'redirect_uri', 'scope', 'application', 'user']


class Oauth2ProviderRefreshtoken(admin.ModelAdmin):
    list_display = ['token', 'access_token', 'application', 'user']

admin.site.register(models.AuthGroup, AuthGroup)
admin.site.register(models.AuthGroupPermissions, AuthGroupPermissions)
admin.site.register(models.AuthPermission, AuthPermission)
admin.site.register(models.AuthUser, AuthUser)
admin.site.register(models.AuthUserGroups, AuthUserGroups)
admin.site.register(models.AuthUserUserPermissions, AuthUserUserPermissions)
admin.site.register(models.AuthtokenToken, AuthtokenToken)
admin.site.register(models.Cliente, Cliente)
admin.site.register(models.DashboardUserdashboardmodule, DashboardUserdashboardmodule)
admin.site.register(models.DjangoAdminLog, DjangoAdminLog)
admin.site.register(models.DjangoContentType, DjangoContentType)
admin.site.register(models.DjangoMigrations, DjangoMigrations)
admin.site.register(models.DjangoSession, DjangoSession)
admin.site.register(models.Estrela, Estrela)
admin.site.register(models.JetBookmark, JetBookmark)
admin.site.register(models.JetPinnedapplication, JetPinnedapplication)
admin.site.register(models.Marca, Marca)
admin.site.register(models.Oauth2ProviderAccesstoken, Oauth2ProviderAccesstoken)
admin.site.register(models.Oauth2ProviderApplication, Oauth2ProviderApplication)
admin.site.register(models.Oauth2ProviderGrant, Oauth2ProviderGrant)
admin.site.register(models.Oauth2ProviderRefreshtoken, Oauth2ProviderRefreshtoken)
