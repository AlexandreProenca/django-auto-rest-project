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
from robot_rest.introspect import IntrospectionError, run_inspectdb
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

    def test_settings_carry_the_connection_details(self, generated):
        dev = (generated.project_dir / "myapi" / "settings" / "dev.py").read_text(encoding="utf-8")
        assert "django.db.backends.sqlite3" in dev

    def test_project_name_is_substituted(self, generated):
        urls = (generated.project_dir / "myapi" / "tests" / "settingstest.py").read_text(encoding="utf-8")
        assert "myapi.settings.tests" in urls


class TestGeneratedRequirements:
    def test_drops_the_dead_generator_dependency(self, generated):
        requirements = (generated.project_dir / "requirements.txt").read_text(encoding="utf-8")
        assert "django-drf-file-generator" not in requirements
        assert "django-auto-rest-project" not in requirements

    def test_uses_a_maintained_mysql_driver(self):
        # MySQL-python e Python 2 e nao instala; o driver segue a engine.
        from robot_rest.render import render

        context = {
            "project_name": "p",
            "secret_key": "k",
            "database": DatabaseConfig(name="d").as_django_dict(),
            "models": [],
        }
        requirements = render("project/requirements.txt.j2", context)
        assert "mysqlclient" in requirements
        assert "MySQL-python" not in requirements


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


class TestDriverErrors:
    def test_missing_driver_raises_introspection_error_not_a_traceback(self):
        # O finally de limpeza ja mascarou este erro com um traceback inteiro.
        database = DatabaseConfig(name="d", user="u", host="192.0.2.1")
        with pytest.raises(IntrospectionError) as excinfo:
            run_inspectdb(database.as_django_dict())
        assert "Nao foi possivel introspectar" in str(excinfo.value)

    def test_missing_driver_suggests_the_extra(self):
        database = DatabaseConfig(name="d", user="u", host="192.0.2.1")
        with pytest.raises(IntrospectionError) as excinfo:
            run_inspectdb(database.as_django_dict())
        assert "django-auto-rest-project[mysql]" in str(excinfo.value)

    def test_cli_reports_one_line_instead_of_a_traceback(self, capsys, tmp_path):
        argv = [
            "-ip",
            "192.0.2.1",
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
