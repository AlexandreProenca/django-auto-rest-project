"""
Teste ponta a ponta: de um banco real ate o projeto gerado.

Usa SQLite porque o inspectdb do Django funciona igual em qualquer backend --
o que permite exercitar o pipeline inteiro sem depender de um MySQL rodando.
"""

import ast
import sqlite3

import pytest

from robot_rest.cli import main
from robot_rest.config import DatabaseConfig, ProjectConfig
from robot_rest.introspect import IntrospectionError, driver_hint, run_inspectdb
from robot_rest.project import ProjectExistsError, generate

SCHEMA = """
CREATE TABLE artist (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);
CREATE TABLE album_track (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    artist_id INTEGER REFERENCES artist(id),
    duration REAL
);
"""


@pytest.fixture(scope="module")
def sqlite_database(tmp_path_factory):
    path = tmp_path_factory.mktemp("db") / "fixture.sqlite3"
    connection = sqlite3.connect(path)
    connection.executescript(SCHEMA)
    connection.commit()
    connection.close()
    return path


@pytest.fixture(scope="module")
def generated(tmp_path_factory, sqlite_database):
    database = DatabaseConfig(name=str(sqlite_database), engine="django.db.backends.sqlite3")
    config = ProjectConfig(project_name="myapi", database=database)
    destination = tmp_path_factory.mktemp("out")
    return generate(config, destination=destination)


class TestInspectdb:
    def test_reads_the_schema(self, sqlite_database):
        database = DatabaseConfig(name=str(sqlite_database), engine="django.db.backends.sqlite3")
        source = run_inspectdb(database.as_django_dict())
        assert "class Artist(models.Model)" in source
        assert "class AlbumTrack(models.Model)" in source

    def test_is_reentrant(self, sqlite_database):
        # Duas introspeccoes no mesmo processo nao podem colidir de alias.
        database = DatabaseConfig(name=str(sqlite_database), engine="django.db.backends.sqlite3")
        first = run_inspectdb(database.as_django_dict())
        second = run_inspectdb(database.as_django_dict())
        assert first == second


class TestGeneratedLayout:
    def test_reports_discovered_models(self, generated):
        assert [m.name for m in generated.models] == ["AlbumTrack", "Artist"]
        assert generated.model_count == 2

    @pytest.mark.parametrize(
        "relative",
        [
            "manage.py",
            "requirements.txt",
            "core/models.py",
            "core/serializers.py",
            "core/views.py",
            "core/urls.py",
            "core/admin.py",
            "myapi/urls.py",
            "myapi/wsgi.py",
            "myapi/settings/__init__.py",
            "myapi/settings/defaults.py",
            "myapi/settings/dev.py",
            "myapi/settings/production.py",
            "myapi/settings/tests.py",
            "myapi/tests/test_rest_api.py",
        ],
    )
    def test_expected_files_exist(self, generated, relative):
        assert (generated.project_dir / relative).is_file()

    def test_startproject_settings_module_is_removed(self, generated):
        # settings.py e o pacote settings/ juntos quebram o import.
        assert not (generated.project_dir / "myapi" / "settings.py").exists()


class TestGeneratedCode:
    @pytest.mark.parametrize(
        "relative",
        [
            "core/models.py",
            "core/serializers.py",
            "core/views.py",
            "core/urls.py",
            "core/admin.py",
            "myapi/urls.py",
            "myapi/settings/defaults.py",
            "myapi/settings/dev.py",
            "myapi/settings/production.py",
            "myapi/settings/tests.py",
            "myapi/settings/__init__.py",
            "myapi/tests/test_rest_api.py",
        ],
    )
    def test_generated_python_is_syntactically_valid(self, generated, relative):
        source = (generated.project_dir / relative).read_text(encoding="utf-8")
        ast.parse(source)

    def test_every_model_has_a_serializer_viewset_and_route(self, generated):
        core = generated.project_dir / "core"
        serializers = (core / "serializers.py").read_text(encoding="utf-8")
        views = (core / "views.py").read_text(encoding="utf-8")
        urls = (core / "urls.py").read_text(encoding="utf-8")

        for model in generated.models:
            assert f"class {model.name}Serializer" in serializers
            assert f"class {model.name}ViewSet" in views
            assert f'basename="{model.basename}"' in urls

    def test_no_unrendered_placeholders_remain(self, generated):
        for path in generated.project_dir.rglob("*.py"):
            assert "@projeto@" not in path.read_text(encoding="utf-8")

    def test_connection_details_live_in_dotenv(self, generated):
        env_file = (generated.project_dir / ".env").read_text(encoding="utf-8")
        assert "DB_ENGINE=django.db.backends.sqlite3" in env_file
        assert "SECRET_KEY=" in env_file

    def test_no_secret_value_is_written_into_a_python_file(self, generated):
        # A versao antiga gravava a SECRET_KEY literal dentro de settings.py.
        env_file = (generated.project_dir / ".env").read_text(encoding="utf-8")
        secret = next(
            line.split("=", 1)[1].strip().strip('"')
            for line in env_file.splitlines()
            if line.startswith("SECRET_KEY=")
        )
        assert len(secret) == 50

        for path in generated.project_dir.rglob("*.py"):
            assert secret not in path.read_text(encoding="utf-8"), path

    def test_settings_read_secrets_from_the_environment(self, generated):
        defaults = (generated.project_dir / "myapi" / "settings" / "defaults.py").read_text(encoding="utf-8")
        assert 'SECRET_KEY = env("SECRET_KEY")' in defaults

    def test_dotenv_is_gitignored_by_the_generated_project(self, generated):
        gitignore = (generated.project_dir / ".gitignore").read_text(encoding="utf-8")
        assert ".env" in gitignore

    def test_dotenv_is_not_world_readable(self, generated):
        mode = (generated.project_dir / ".env").stat().st_mode & 0o777
        assert mode == 0o600, oct(mode)

    def test_env_example_carries_no_real_credentials(self, generated):
        example = (generated.project_dir / ".env.example").read_text(encoding="utf-8")
        assert "fixture.sqlite3" not in example

    def test_project_name_is_substituted(self, generated):
        urls = (generated.project_dir / "myapi" / "tests" / "settingstest.py").read_text(encoding="utf-8")
        assert "myapi.settings.tests" in urls


class TestModernDjango:
    """Regressoes contra as APIs que o Phase 2 removeu."""

    REMOVED_APIS = [
        "django.conf.urls",  # url() sumiu no Django 4.0
        "include(admin.site.urls)",
        "django.contrib.auth.views.password_reset",
        "oauth2_provider.ext.rest_framework",  # virou .contrib no DOT 1.0
        "social.apps.django_app",  # virou social_django
        "rest_framework_swagger",  # projeto descontinuado
        "MIDDLEWARE_CLASSES",
    ]

    @pytest.mark.parametrize("api", REMOVED_APIS)
    def test_generated_project_uses_no_removed_api(self, generated, api):
        for path in generated.project_dir.rglob("*.py"):
            assert api not in path.read_text(encoding="utf-8"), f"{path} usa {api}"

    def test_urls_use_path_not_url(self, generated):
        urls = (generated.project_dir / "myapi" / "urls.py").read_text(encoding="utf-8")
        assert "from django.urls import" in urls
        assert 'path("admin/", admin.site.urls)' in urls

    def test_schema_is_served_by_spectacular(self, generated):
        urls = (generated.project_dir / "myapi" / "urls.py").read_text(encoding="utf-8")
        assert "drf_spectacular" in urls
        assert 'name="schema"' in urls


class TestGeneratedSecurity:
    def test_no_hardcoded_personal_email(self, generated):
        # defaults.tpl embutia o e-mail pessoal do autor em todo projeto gerado.
        for path in generated.project_dir.rglob("*.py"):
            assert "linuxloco@gmail.com" not in path.read_text(encoding="utf-8")

    def test_cors_is_not_wide_open(self, generated):
        defaults = (generated.project_dir / "myapi" / "settings" / "defaults.py").read_text(encoding="utf-8")
        assert "CORS_ORIGIN_ALLOW_ALL" not in defaults
        assert "CORS_ALLOWED_ORIGINS" in defaults

    def test_allowed_hosts_is_not_a_wildcard(self, generated):
        for name in ("defaults.py", "dev.py", "production.py"):
            source = (generated.project_dir / "myapi" / "settings" / name).read_text(encoding="utf-8")
            assert 'ALLOWED_HOSTS = ["*"]' not in source
            assert "ALLOWED_HOSTS = ['*']" not in source

    def test_default_permission_requires_authentication(self, generated):
        defaults = (generated.project_dir / "myapi" / "settings" / "defaults.py").read_text(encoding="utf-8")
        assert "rest_framework.permissions.IsAuthenticated" in defaults

    def test_production_settings_harden_cookies_and_tls(self, generated):
        production = (generated.project_dir / "myapi" / "settings" / "production.py").read_text(
            encoding="utf-8"
        )
        for setting in ("SESSION_COOKIE_SECURE", "CSRF_COOKIE_SECURE", "SECURE_HSTS_SECONDS"):
            assert setting in production


class TestGeneratedRequirements:
    def test_drops_the_dead_generator_dependency(self, generated):
        requirements = (generated.project_dir / "requirements.txt").read_text(encoding="utf-8")
        assert "django-drf-file-generator" not in requirements
        assert "django-auto-rest-project" not in requirements

    def test_uses_a_maintained_mysql_driver(self):
        # MySQL-python e Python 2 e nao instala; o driver segue a engine.
        requirements = self.render_requirements("django.db.backends.mysql")
        assert "mysqlclient" in requirements
        assert "MySQL-python" not in requirements

    def test_postgres_engine_gets_psycopg(self):
        requirements = self.render_requirements("django.db.backends.postgresql")
        assert "psycopg[binary]" in requirements
        assert "mysqlclient" not in requirements

    @pytest.mark.parametrize(
        "package",
        ["django-jet", "django-rest-swagger", "django-rest-auth", "django-social-auth", "openapi-codec"],
    )
    def test_dead_packages_are_gone(self, generated, package):
        requirements = (generated.project_dir / "requirements.txt").read_text(encoding="utf-8")
        # Comparacao por linha: "django-rest-auth" nao pode casar num comentario.
        declared = [line.strip() for line in requirements.splitlines() if not line.strip().startswith("#")]
        assert not any(line.startswith(package) for line in declared)

    def test_install_set_is_small(self, generated):
        requirements = (generated.project_dir / "requirements.txt").read_text(encoding="utf-8")
        declared = [
            line.strip()
            for line in requirements.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        # Eram 27 pacotes antes do Phase 2.
        assert len(declared) <= 8, declared

    @staticmethod
    def render_requirements(engine):
        from robot_rest.render import render

        return render(
            "project/requirements.txt.j2",
            {
                "project_name": "p",
                "secret_key": "k",
                "database": DatabaseConfig(name="d", engine=engine).as_django_dict(),
                "models": [],
            },
        )


class TestSafety:
    def test_refuses_to_overwrite_an_existing_directory(self, tmp_path, sqlite_database):
        (tmp_path / "myapi").mkdir()
        database = DatabaseConfig(name=str(sqlite_database), engine="django.db.backends.sqlite3")
        config = ProjectConfig(project_name="myapi", database=database)
        with pytest.raises(ProjectExistsError):
            generate(config, destination=tmp_path)

    def test_generates_into_the_current_directory(self, tmp_path, sqlite_database, monkeypatch):
        # Caso padrao da CLI (sem -o) e o que mais quebrou: um diretorio vazio
        # no cwd vira namespace package e o startproject recusa o nome.
        monkeypatch.chdir(tmp_path)
        database = DatabaseConfig(name=str(sqlite_database), engine="django.db.backends.sqlite3")
        config = ProjectConfig(project_name="cwdproj", database=database)

        result = generate(config)

        assert result.project_dir == tmp_path / "cwdproj"
        assert (result.project_dir / "manage.py").is_file()
        assert (result.project_dir / "core" / "serializers.py").is_file()

    def test_leaves_no_staging_directory_behind(self, tmp_path, sqlite_database, monkeypatch):
        monkeypatch.chdir(tmp_path)
        database = DatabaseConfig(name=str(sqlite_database), engine="django.db.backends.sqlite3")
        generate(ProjectConfig(project_name="tidyproj", database=database))
        assert [p.name for p in tmp_path.iterdir()] == ["tidyproj"]

    def test_cleans_up_after_a_failure_mid_render(self, tmp_path, sqlite_database, monkeypatch):
        # Falha depois do scaffold: o diretorio parcial nao pode sobrar.
        # A versao antiga deixava um projeto pela metade no disco.
        from robot_rest import project as project_module

        def explode(*args, **kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(project_module, "render_project", explode)

        database = DatabaseConfig(name=str(sqlite_database), engine="django.db.backends.sqlite3")
        config = ProjectConfig(project_name="doomed", database=database)

        with pytest.raises(RuntimeError, match="boom"):
            generate(config, destination=tmp_path)
        assert not (tmp_path / "doomed").exists()

    def test_connection_failure_creates_nothing(self, tmp_path):
        # A introspeccao roda antes do scaffold, entao o erro mais comum
        # (conexao/senha/driver) nao chega a tocar o disco.
        database = DatabaseConfig(name="/nonexistent/dir/db.sqlite3", engine="django.db.backends.sqlite3")
        config = ProjectConfig(project_name="doomed", database=database)
        with pytest.raises(IntrospectionError):
            generate(config, destination=tmp_path)
        assert list(tmp_path.iterdir()) == []


#: Porta fechada em loopback: recusa na hora, sem esperar timeout.
#: Um IP inalcancavel deixaria cada um destes testes travado por minutos.
UNREACHABLE = {"host": "127.0.0.1", "port": "1"}


class TestDriverErrors:
    def test_connection_failure_raises_introspection_error_not_a_traceback(self):
        # O finally de limpeza ja mascarou este erro com um traceback inteiro.
        database = DatabaseConfig(name="d", user="u", **UNREACHABLE)
        with pytest.raises(IntrospectionError) as excinfo:
            run_inspectdb(database.as_django_dict())
        assert "Nao foi possivel introspectar" in str(excinfo.value)

    @pytest.mark.parametrize(
        ("engine", "extra"),
        [
            ("django.db.backends.mysql", "mysql"),
            ("django.db.backends.postgresql", "postgres"),
        ],
    )
    def test_missing_driver_suggests_the_extra(self, engine, extra):
        # Funcao pura: a versao anterior so passava quando o driver estava
        # ausente da maquina, entao quebrava dentro do container de teste.
        hint = driver_hint(engine, ModuleNotFoundError("No module named 'MySQLdb'"))
        assert f"django-auto-rest-project[{extra}]" in hint

    def test_no_driver_hint_for_unrelated_errors(self):
        assert driver_hint("django.db.backends.mysql", RuntimeError("access denied")) == ""

    def test_no_driver_hint_for_sqlite(self):
        assert driver_hint("django.db.backends.sqlite3", ModuleNotFoundError("no module")) == ""

    def test_cli_reports_one_line_instead_of_a_traceback(self, capsys, tmp_path):
        argv = [
            "-ip",
            UNREACHABLE["host"],
            "-port",
            UNREACHABLE["port"],
            "-user",
            "u",
            "-database",
            "d",
            "-project",
            "failproj",
            "-password",
            "p",
            "-o",
            str(tmp_path),
        ]
        assert main(argv) == 1
        captured = capsys.readouterr()
        assert captured.err.startswith("erro:")
        assert "Traceback" not in captured.err
