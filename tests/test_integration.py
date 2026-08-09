"""
Testes de integracao contra bancos reais em container.

    docker compose up -d
    ROBOT_REST_TEST_MYSQL=1 ROBOT_REST_TEST_POSTGRES=1 python -m pytest
    docker compose down -v

Sem as variaveis de ambiente os testes sao pulados, entao a suite continua
rodando sem Docker. O SQLite ja e coberto em test_generate.py; o valor aqui e
exercitar MySQL e PostgreSQL de verdade -- drivers, tipos de coluna e chaves
estrangeiras que o SQLite nao reproduz.
"""

import ast
import os

import pytest

from robot_rest.config import (
    MYSQL_ENGINE,
    POSTGRES_ENGINE,
    DatabaseConfig,
    ProjectConfig,
)
from robot_rest.introspect import discover_models, introspect_schema, list_tables
from robot_rest.project import generate

#: Senha com '#' de proposito: sem aspas, o django-environ leria o resto da
#: linha do .env como comentario.
FIXTURE_PASSWORD = "s3cr3t#pass"

ENGINES = {
    "mysql": {
        "flag": "ROBOT_REST_TEST_MYSQL",
        "engine": MYSQL_ENGINE,
        "host_var": "ROBOT_REST_MYSQL_HOST",
        "port_var": "ROBOT_REST_MYSQL_PORT",
        "default_host": "127.0.0.1",
        "default_port": "13306",
    },
    "postgres": {
        "flag": "ROBOT_REST_TEST_POSTGRES",
        "engine": POSTGRES_ENGINE,
        "host_var": "ROBOT_REST_POSTGRES_HOST",
        "port_var": "ROBOT_REST_POSTGRES_PORT",
        "default_host": "127.0.0.1",
        "default_port": "15432",
    },
}


def database_for(name):
    """Monta a conexao do banco em container, ou pula o teste."""
    spec = ENGINES[name]
    if not os.environ.get(spec["flag"]):
        pytest.skip(f"{spec['flag']} nao definido; suba os containers com 'docker compose up -d'")

    return DatabaseConfig(
        name="shopdb",
        user="appuser",
        password=FIXTURE_PASSWORD,
        host=os.environ.get(spec["host_var"], spec["default_host"]),
        port=os.environ.get(spec["port_var"], spec["default_port"]),
        engine=spec["engine"],
    )


@pytest.fixture(params=sorted(ENGINES))
def engine_name(request):
    return request.param


@pytest.fixture
def database(engine_name):
    return database_for(engine_name)


@pytest.fixture
def generated(database, engine_name, tmp_path):
    config = ProjectConfig(project_name=f"{engine_name}api", database=database)
    return generate(config, destination=tmp_path)


class TestLiveIntrospection:
    def test_reaches_the_server_and_lists_tables(self, database):
        assert set(list_tables(database.as_django_dict())) >= {"customer", "order_item"}

    def test_discovers_the_fixture_models(self, database):
        schema = introspect_schema(database.as_django_dict())
        assert [m.name for m in discover_models(schema.models_source)] == ["Customer", "OrderItem"]

    def test_foreign_key_is_mapped(self, database):
        schema = introspect_schema(database.as_django_dict())
        assert "ForeignKey" in schema.models_source

    def test_models_are_unmanaged_by_default(self, database):
        schema = introspect_schema(database.as_django_dict())
        assert "managed = False" in schema.models_source


class TestLiveGeneration:
    def test_generates_the_expected_models(self, generated):
        assert [m.name for m in generated.models] == ["Customer", "OrderItem"]

    def test_routes_are_registered(self, generated):
        urls = (generated.project_dir / "core" / "urls.py").read_text(encoding="utf-8")
        assert 'router.register(r"customer"' in urls
        assert 'router.register(r"order-item"' in urls

    @pytest.mark.parametrize(
        "relative",
        ["core/models.py", "core/serializers.py", "core/views.py", "core/urls.py", "core/admin.py"],
    )
    def test_generated_python_is_valid(self, generated, relative):
        ast.parse((generated.project_dir / relative).read_text(encoding="utf-8"))

    def test_driver_matches_the_engine(self, generated, engine_name):
        requirements = (generated.project_dir / "requirements.txt").read_text(encoding="utf-8")
        expected = "mysqlclient" if engine_name == "mysql" else "psycopg"
        assert expected in requirements


class TestPasswordSurvivesDotenv:
    """
    A senha do fixture tem '#'. Sem as aspas do filtro envquote, o
    django-environ trataria o resto da linha como comentario e o projeto
    gerado tentaria conectar com uma senha truncada.
    """

    def test_password_is_quoted_in_dotenv(self, generated):
        env_file = (generated.project_dir / ".env").read_text(encoding="utf-8")
        assert f'DB_PASSWORD="{FIXTURE_PASSWORD}"' in env_file

    def test_generated_settings_read_back_the_full_password(self, generated):
        import environ

        env = environ.Env()
        environ.Env.read_env(str(generated.project_dir / ".env"))
        assert env("DB_PASSWORD") == FIXTURE_PASSWORD


class TestEnginesAgree:
    """MySQL e PostgreSQL devem produzir os mesmos modelos e rotas."""

    def test_same_models_from_both_engines(self):
        names = {}
        for name in ENGINES:
            database = database_for(name)
            schema = introspect_schema(database.as_django_dict())
            names[name] = [m.name for m in discover_models(schema.models_source)]
        assert names["mysql"] == names["postgres"]
