"""Testes do suporte multi-banco e da flag --managed."""

import pytest

from robot_rest.cli import build_config, build_parser
from robot_rest.config import (
    MYSQL_ENGINE,
    POSTGRES_ENGINE,
    SQLITE_ENGINE,
    ConfigError,
    DatabaseConfig,
    ProjectConfig,  # noqa: E402
    needs_credentials,
    resolve_engine,
    validate_database_config,
)
from robot_rest.introspect import set_managed

INSPECTDB_META = """\
class Artist(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'artist'
"""


class TestResolveEngine:
    @pytest.mark.parametrize(
        ("alias", "expected"),
        [
            ("mysql", MYSQL_ENGINE),
            ("mariadb", MYSQL_ENGINE),
            ("postgres", POSTGRES_ENGINE),
            ("postgresql", POSTGRES_ENGINE),
            ("sqlite", SQLITE_ENGINE),
            ("sqlite3", SQLITE_ENGINE),
        ],
    )
    def test_known_aliases(self, alias, expected):
        assert resolve_engine(alias) == expected

    @pytest.mark.parametrize("alias", ["MySQL", " postgres ", "SQLITE"])
    def test_is_case_and_space_insensitive(self, alias):
        assert resolve_engine(alias).startswith("django.db.backends.")

    def test_unknown_engine_lists_the_supported_ones(self):
        with pytest.raises(ConfigError) as excinfo:
            resolve_engine("oracle")
        assert "mysql" in str(excinfo.value)
        assert "sqlite" in str(excinfo.value)


class TestNeedsCredentials:
    def test_server_engines_need_credentials(self):
        assert needs_credentials(MYSQL_ENGINE)
        assert needs_credentials(POSTGRES_ENGINE)

    def test_sqlite_is_a_local_file(self):
        assert not needs_credentials(SQLITE_ENGINE)


class TestValidateDatabaseConfig:
    def test_sqlite_needs_only_a_path(self):
        database = DatabaseConfig(name="/tmp/app.sqlite3", engine=SQLITE_ENGINE)
        assert validate_database_config(database) is database

    @pytest.mark.parametrize("engine", [MYSQL_ENGINE, POSTGRES_ENGINE])
    def test_server_engines_require_host_and_user(self, engine):
        with pytest.raises(ConfigError) as excinfo:
            validate_database_config(DatabaseConfig(name="db", engine=engine))
        assert "-ip" in str(excinfo.value)
        assert "-user" in str(excinfo.value)

    def test_missing_host_only(self):
        with pytest.raises(ConfigError, match="-ip"):
            validate_database_config(DatabaseConfig(name="db", user="u", engine=MYSQL_ENGINE))

    def test_empty_database_name_is_rejected(self):
        with pytest.raises(ConfigError, match="-database"):
            validate_database_config(DatabaseConfig(name="", user="u", host="h"))

    def test_sqlite_error_mentions_a_file_path(self):
        with pytest.raises(ConfigError, match="caminho do arquivo"):
            validate_database_config(DatabaseConfig(name="", engine=SQLITE_ENGINE))


class TestPortDefaults:
    @pytest.mark.parametrize(
        ("engine", "port"),
        [(MYSQL_ENGINE, "3306"), (POSTGRES_ENGINE, "5432"), (SQLITE_ENGINE, "")],
    )
    def test_default_port_per_engine(self, engine, port):
        assert DatabaseConfig(name="d", engine=engine).as_django_dict()["PORT"] == port


class TestCliEngineArgument:
    def test_defaults_to_mysql(self):
        args = build_parser().parse_args(["-ip", "h", "-user", "u", "-database", "d", "-project", "p"])
        assert args.engine == "mysql"

    def test_sqlite_needs_no_host_or_user(self):
        args = build_parser().parse_args(["-engine", "sqlite", "-database", "app.sqlite3", "-project", "p"])
        config = build_config(args, password="")
        assert config.database.engine == SQLITE_ENGINE

    def test_sqlite_path_is_made_absolute(self, tmp_path, monkeypatch):
        # O projeto gerado roda de outro diretorio; um caminho relativo
        # apontaria para o lugar errado depois de gravado no .env.
        monkeypatch.chdir(tmp_path)
        args = build_parser().parse_args(["-engine", "sqlite", "-database", "app.sqlite3", "-project", "p"])
        config = build_config(args, password="")
        assert config.database.name == str(tmp_path.resolve() / "app.sqlite3")

    def test_postgres_engine_reaches_the_config(self):
        args = build_parser().parse_args(
            ["-engine", "postgres", "-ip", "h", "-user", "u", "-database", "d", "-project", "p"]
        )
        assert build_config(args, "pw").database.as_django_dict()["ENGINE"] == POSTGRES_ENGINE

    def test_unsupported_engine_is_rejected_by_argparse(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args(["-engine", "oracle", "-database", "d", "-project", "p"])

    def test_missing_host_for_mysql_is_a_config_error(self):
        args = build_parser().parse_args(["-database", "d", "-project", "p"])
        with pytest.raises(ConfigError):
            build_config(args, "pw")


class TestSqliteSkipsPasswordPrompt:
    def test_main_does_not_prompt_for_sqlite(self, tmp_path, monkeypatch):
        # Um prompt travaria a geracao de um banco que nem tem senha.
        import robot_rest.cli as cli_module

        def explode(*args, **kwargs):
            raise AssertionError("nao deveria pedir senha para sqlite")

        monkeypatch.setattr(cli_module.getpass, "getpass", explode)
        monkeypatch.delenv("ROBOT_REST_DB_PASSWORD", raising=False)

        import sqlite3

        db = tmp_path / "app.sqlite3"
        connection = sqlite3.connect(db)
        connection.executescript("CREATE TABLE thing (id INTEGER PRIMARY KEY);")
        connection.commit()
        connection.close()

        exit_code = cli_module.main(
            ["-engine", "sqlite", "-database", str(db), "-project", "nopw", "-o", str(tmp_path)]
        )
        assert exit_code == 0
        assert (tmp_path / "nopw" / "manage.py").is_file()


class TestSetManaged:
    def test_unmanaged_is_the_default_and_leaves_source_alone(self):
        assert set_managed(INSPECTDB_META, managed=False) == INSPECTDB_META

    def test_managed_flips_the_meta_option(self):
        result = set_managed(INSPECTDB_META, managed=True)
        assert "managed = True" in result
        assert "managed = False" not in result

    def test_preserves_indentation(self):
        result = set_managed(INSPECTDB_META, managed=True)
        assert "        managed = True" in result

    def test_leaves_other_lines_untouched(self):
        result = set_managed(INSPECTDB_META, managed=True)
        assert "db_table = 'artist'" in result
        assert "name = models.CharField(max_length=100)" in result

    def test_handles_several_models(self):
        source = INSPECTDB_META + "\n" + INSPECTDB_META.replace("Artist", "Album")
        assert set_managed(source, managed=True).count("managed = True") == 2


def sqlite_database_dict(path):
    return DatabaseConfig(name=str(path), engine=SQLITE_ENGINE).as_django_dict()


@pytest.fixture(scope="module")
def polluted_database(tmp_path_factory):
    """Banco de usuario que ja tem as tabelas do proprio Django dentro."""
    import sqlite3

    path = tmp_path_factory.mktemp("polluted") / "app.sqlite3"
    connection = sqlite3.connect(path)
    connection.executescript(
        "CREATE TABLE customer (id INTEGER PRIMARY KEY, email VARCHAR(200));"
        "CREATE TABLE auth_user (id INTEGER PRIMARY KEY, username VARCHAR(150));"
        "CREATE TABLE django_session (session_key VARCHAR(40) PRIMARY KEY);"
        "CREATE TABLE django_migrations (id INTEGER PRIMARY KEY, app VARCHAR(255));"
    )
    connection.commit()
    connection.close()
    return path


class TestDjangoSystemTables:
    """
    O banco alvo pode ja ter as tabelas do proprio Django -- inclusive porque
    o usuario rodou migrate num projeto gerado antes. Sem filtro, o inspectdb
    devolveria auth_user e django_session como modelos.
    """

    def test_system_tables_are_skipped_by_default(self, polluted_database):
        from robot_rest.introspect import discover_models, introspect_schema

        schema = introspect_schema(sqlite_database_dict(polluted_database))
        assert [m.name for m in discover_models(schema.models_source)] == ["Customer"]

    def test_skipped_tables_are_reported(self, polluted_database):
        from robot_rest.introspect import introspect_schema

        schema = introspect_schema(sqlite_database_dict(polluted_database))
        assert set(schema.skipped_tables) == {"auth_user", "django_migrations", "django_session"}

    def test_all_tables_opt_in_includes_them(self, polluted_database):
        from robot_rest.introspect import discover_models, introspect_schema

        schema = introspect_schema(sqlite_database_dict(polluted_database), include_system_tables=True)
        names = {m.name for m in discover_models(schema.models_source)}
        assert "AuthUser" in names
        assert schema.skipped_tables == ()

    def test_database_with_only_system_tables_yields_no_models(self, tmp_path):
        import sqlite3

        from robot_rest.introspect import discover_models, introspect_schema

        path = tmp_path / "only_django.sqlite3"
        connection = sqlite3.connect(path)
        connection.executescript("CREATE TABLE auth_user (id INTEGER PRIMARY KEY);")
        connection.commit()
        connection.close()

        # Sem tabelas restantes, chamar o inspectdb sem argumentos traria o
        # banco inteiro de volta -- o filtro ficaria sem efeito.
        schema = introspect_schema(sqlite_database_dict(path))
        assert discover_models(schema.models_source) == []
        assert schema.skipped_tables == ("auth_user",)

    def test_generated_project_has_no_auth_routes(self, polluted_database, tmp_path):
        from robot_rest.project import generate

        config = ProjectConfig(
            project_name="cleanapi",
            database=DatabaseConfig(name=str(polluted_database), engine=SQLITE_ENGINE),
        )
        result = generate(config, destination=tmp_path)
        urls = (result.project_dir / "core" / "urls.py").read_text(encoding="utf-8")
        assert "auth-user" not in urls
        assert "django-session" not in urls
        assert "customer" in urls
