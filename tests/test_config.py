"""Testes da configuracao e da validacao de entrada."""

import string

import pytest

from robot_rest.config import (
    SECRET_KEY_LENGTH,
    ConfigError,
    DatabaseConfig,
    ProjectConfig,
    generate_secret_key,
    validate_project_name,
)


class TestSecretKey:
    def test_has_requested_length(self):
        assert len(generate_secret_key()) == SECRET_KEY_LENGTH
        assert len(generate_secret_key(12)) == 12

    def test_uses_only_alphanumerics(self):
        assert set(generate_secret_key(500)) <= set(string.ascii_letters + string.digits)

    def test_keys_are_not_repeated(self):
        assert generate_secret_key() != generate_secret_key()


class TestValidateProjectName:
    @pytest.mark.parametrize("name", ["myapi", "my_api", "api2", "_private"])
    def test_accepts_valid_identifiers(self, name):
        assert validate_project_name(name) == name

    @pytest.mark.parametrize("name", ["", "my-api", "2api", "my api", "my.api"])
    def test_rejects_invalid_identifiers(self, name):
        with pytest.raises(ConfigError):
            validate_project_name(name)

    @pytest.mark.parametrize("name", ["class", "import", "lambda"])
    def test_rejects_python_keywords(self, name):
        with pytest.raises(ConfigError):
            validate_project_name(name)


class TestDatabaseConfig:
    def test_builds_django_dict(self):
        db = DatabaseConfig(name="appdb", user="u", password="p", host="h", port="3307")
        assert db.as_django_dict() == {
            "ENGINE": "django.db.backends.mysql",
            "NAME": "appdb",
            "USER": "u",
            "PASSWORD": "p",
            "HOST": "h",
            "PORT": "3307",
        }

    def test_fills_default_port_per_engine(self):
        assert DatabaseConfig(name="d").as_django_dict()["PORT"] == "3306"
        postgres = DatabaseConfig(name="d", engine="django.db.backends.postgresql")
        assert postgres.as_django_dict()["PORT"] == "5432"

    def test_explicit_port_wins(self):
        assert DatabaseConfig(name="d", port="9999").as_django_dict()["PORT"] == "9999"


class TestProjectConfig:
    def test_validates_name_on_construction(self):
        with pytest.raises(ConfigError):
            ProjectConfig(project_name="my-api", database=DatabaseConfig(name="d"))

    def test_generates_a_secret_key_per_project(self):
        a = ProjectConfig(project_name="a", database=DatabaseConfig(name="d"))
        b = ProjectConfig(project_name="b", database=DatabaseConfig(name="d"))
        assert a.secret_key != b.secret_key
        assert len(a.secret_key) == SECRET_KEY_LENGTH

    def test_template_context_shape(self):
        config = ProjectConfig(project_name="myapi", database=DatabaseConfig(name="appdb"))
        context = config.as_template_context()
        assert context["project_name"] == "myapi"
        assert context["database"]["NAME"] == "appdb"
        assert context["secret_key"] == config.secret_key
