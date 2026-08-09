"""Testes das paginas de conta geradas e do descarte de modelos quebrados."""

import sqlite3

import pytest

from robot_rest.cli import build_config, build_parser
from robot_rest.config import DatabaseConfig, ProjectConfig
from robot_rest.introspect import prune_broken_models
from robot_rest.project import AUTH_TEMPLATES, generate

#: Nomes que o django-registration procura. Errar um so aparece quando o
#: usuario abre a pagina: TemplateDoesNotExist em producao.
REGISTRATION_TEMPLATES = {
    "templates/django_registration/registration_form.html",
    "templates/django_registration/registration_complete.html",
    "templates/django_registration/registration_closed.html",
    "templates/django_registration/activation_form.html",
    "templates/django_registration/activation_complete.html",
    "templates/django_registration/activation_email_subject.txt",
    "templates/django_registration/activation_email_body.txt",
}

#: django.contrib.auth nao traz registration/login.html; sem ele o login 500.
AUTH_VIEW_TEMPLATES = {
    "templates/registration/login.html",
    "templates/registration/logged_out.html",
    "templates/registration/password_reset_form.html",
    "templates/registration/password_reset_done.html",
    "templates/registration/password_reset_confirm.html",
    "templates/registration/password_reset_complete.html",
    "templates/registration/password_change_form.html",
    "templates/registration/password_change_done.html",
}


@pytest.fixture(scope="module")
def database(tmp_path_factory):
    path = tmp_path_factory.mktemp("authdb") / "app.sqlite3"
    connection = sqlite3.connect(path)
    connection.executescript("CREATE TABLE product (id INTEGER PRIMARY KEY, name VARCHAR(80));")
    connection.commit()
    connection.close()
    return DatabaseConfig(name=str(path), engine="django.db.backends.sqlite3")


@pytest.fixture(scope="module")
def with_auth(tmp_path_factory, database):
    config = ProjectConfig(project_name="withauth", database=database)
    return generate(config, destination=tmp_path_factory.mktemp("withauth"))


@pytest.fixture(scope="module")
def without_auth(tmp_path_factory, database):
    config = ProjectConfig(project_name="withoutauth", database=database, auth_enabled=False)
    return generate(config, destination=tmp_path_factory.mktemp("withoutauth"))


class TestDefaults:
    def test_auth_is_on_by_default(self):
        args = build_parser().parse_args(["-ip", "h", "-user", "u", "-database", "d", "-project", "p"])
        assert build_config(args, "pw").auth_enabled is True

    def test_no_auth_turns_it_off(self):
        args = build_parser().parse_args(
            ["-ip", "h", "-user", "u", "-database", "d", "-project", "p", "--no-auth"]
        )
        assert build_config(args, "pw").auth_enabled is False


class TestGeneratedTemplates:
    @pytest.mark.parametrize("relative", sorted(REGISTRATION_TEMPLATES | AUTH_VIEW_TEMPLATES))
    def test_template_is_generated(self, with_auth, relative):
        assert (with_auth.project_dir / relative).is_file()

    def test_every_auth_template_is_declared(self):
        outputs = set(AUTH_TEMPLATES.values())
        assert REGISTRATION_TEMPLATES | AUTH_VIEW_TEMPLATES <= outputs

    def test_templates_are_absent_without_auth(self, without_auth):
        assert not (without_auth.project_dir / "templates").exists()


class TestGeneratedSettings:
    def settings(self, result):
        name = result.project_dir.name
        return (result.project_dir / name / "settings" / "defaults.py").read_text(encoding="utf-8")

    def test_registration_app_is_installed(self, with_auth):
        assert '"django_registration"' in self.settings(with_auth)

    def test_template_dir_is_configured(self, with_auth):
        # Sem DIRS o Django nao acha nenhum dos templates gerados.
        assert 'BASE_DIR / "templates"' in self.settings(with_auth)

    def test_login_does_not_redirect_to_a_missing_page(self, with_auth):
        # O projeto gerado nao tem view na raiz: redirecionar para "/" dava
        # 404 logo depois de entrar.
        settings = self.settings(with_auth)
        assert 'LOGIN_REDIRECT_URL = "/"' not in settings
        assert 'LOGIN_REDIRECT_URL = "/v1/"' in settings

    def test_logout_lands_on_the_login_page(self, with_auth):
        assert 'LOGOUT_REDIRECT_URL = "/accounts/login/"' in self.settings(with_auth)

    def test_activation_window_is_configurable(self, with_auth):
        assert "ACCOUNT_ACTIVATION_DAYS" in self.settings(with_auth)

    def test_nothing_registration_related_without_auth(self, without_auth):
        assert "django_registration" not in self.settings(without_auth)


class TestGeneratedUrls:
    def urls(self, result):
        name = result.project_dir.name
        return (result.project_dir / name / "urls.py").read_text(encoding="utf-8")

    def test_registration_urls_are_included(self, with_auth):
        assert "django_registration.backends.activation.urls" in self.urls(with_auth)

    def test_django_auth_urls_are_included(self, with_auth):
        assert 'include("django.contrib.auth.urls")' in self.urls(with_auth)

    def test_no_registration_urls_without_auth(self, without_auth):
        assert "django_registration" not in self.urls(without_auth)


class TestActivationEmail:
    def test_link_uses_the_querystring_form(self, with_auth):
        # Na 5.x a rota de ativacao nao recebe a chave no caminho; montar o
        # link do jeito antigo quebra com NoReverseMatch ao enviar o e-mail.
        body = (
            with_auth.project_dir / "templates" / "django_registration" / "activation_email_body.txt"
        ).read_text(encoding="utf-8")
        assert "?activation_key={{ activation_key }}" in body
        assert "activation_key=activation_key" not in body


class TestGeneratedTests:
    def test_account_tests_are_generated(self, with_auth):
        path = with_auth.project_dir / "withauth" / "tests" / "test_accounts.py"
        assert path.is_file()
        assert "TestCadastro" in path.read_text(encoding="utf-8")

    def test_absent_without_auth(self, without_auth):
        assert not (without_auth.project_dir / "withoutauth" / "tests" / "test_accounts.py").exists()


class TestPruneBrokenModels:
    """
    Filtrar as tabelas do Django pode deixar uma tabela de terceiros
    apontando para o vazio. O models.py resultante nao carrega.
    """

    SOURCE = """\
from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=80)


class SocialappSites(models.Model):
    site = models.ForeignKey(DjangoSite, models.DO_NOTHING)


class Dependent(models.Model):
    parent = models.ForeignKey(SocialappSites, models.DO_NOTHING)
"""

    def test_drops_models_pointing_at_missing_tables(self):
        source, dropped = prune_broken_models(self.SOURCE)
        assert "SocialappSites" in dropped
        assert "class SocialappSites" not in source

    def test_drops_cascading_dependents(self):
        # Dependent apontava para um modelo que acabou de sair.
        _, dropped = prune_broken_models(self.SOURCE)
        assert set(dropped) == {"SocialappSites", "Dependent"}

    def test_keeps_healthy_models(self):
        source, _ = prune_broken_models(self.SOURCE)
        assert "class Customer" in source

    def test_leaves_a_clean_file_untouched(self):
        clean = "from django.db import models\n\n\nclass Customer(models.Model):\n    pass\n"
        assert prune_broken_models(clean) == (clean, ())

    def test_self_reference_is_not_broken(self):
        source = (
            "from django.db import models\n\n\n"
            "class Node(models.Model):\n"
            "    parent = models.ForeignKey('self', models.DO_NOTHING)\n"
        )
        assert prune_broken_models(source) == (source, ())

    def test_valid_cross_reference_survives(self):
        source = (
            "from django.db import models\n\n\n"
            "class Author(models.Model):\n    pass\n\n\n"
            "class Book(models.Model):\n"
            "    author = models.ForeignKey(Author, models.DO_NOTHING)\n"
        )
        assert prune_broken_models(source) == (source, ())
