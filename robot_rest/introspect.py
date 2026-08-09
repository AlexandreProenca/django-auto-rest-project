"""
Descoberta dos modelos do banco.

Substitui o ``django-drf-file-generator`` (``drf_gen``), sem release desde
2016. Sao dois passos independentes e testaveis:

1. :func:`run_inspectdb` roda o ``inspectdb`` do proprio Django em processo,
   sem subprocess e sem precisar de um ``settings.py`` no disco.
2. :func:`discover_models` le o codigo gerado com o modulo ``ast``, sem
   importar nada, e devolve os modelos encontrados.
"""

from __future__ import annotations

import ast
import io
import itertools
import re
from contextlib import contextmanager
from dataclasses import dataclass

_ALIAS_COUNTER = itertools.count()

#: Tabelas do proprio Django (contrib + authtoken).
#:
#: Se o banco alvo ja foi usado por um projeto Django -- inclusive um gerado
#: por este robot e migrado depois --, o inspectdb enxerga essas tabelas e
#: geraria modelos duplicados. Com ``--managed`` isso vira erro (models.E028,
#: "db_table is used by multiple models"), e mesmo sem ele o resultado seria
#: publicar auth_user e django_session como rotas REST.
DJANGO_SYSTEM_TABLES = frozenset(
    {
        "auth_group",
        "auth_group_permissions",
        "auth_permission",
        "auth_user",
        "auth_user_groups",
        "auth_user_user_permissions",
        "authtoken_token",
        "django_admin_log",
        "django_content_type",
        "django_migrations",
        "django_session",
        "django_site",
    }
)

_CAMEL_BOUNDARY = re.compile(r"(.)([A-Z][a-z]+)")
_CAMEL_TAIL = re.compile(r"([a-z0-9])([A-Z])")


#: Extra do pacote que instala o driver de cada engine.
DRIVER_EXTRAS = {
    "django.db.backends.mysql": "mysql",
    "django.db.backends.postgresql": "postgres",
}


#: models.py gerado quando o banco nao tem nenhuma tabela de usuario.
EMPTY_MODELS_SOURCE = "# Nenhuma tabela encontrada no banco.\nfrom django.db import models  # noqa: F401\n"


class IntrospectionError(RuntimeError):
    """O banco nao pode ser introspectado."""


def driver_hint(engine: str, exc: Exception) -> str:
    """
    Sugere a instalacao do driver quando esse for o motivo da falha.

    Os drivers sao extras opcionais, entao a falha por driver ausente e
    esperada e merece uma instrucao em vez de um traceback.
    """
    extra = DRIVER_EXTRAS.get(engine)
    if not extra or "module" not in str(exc).lower():
        return ""
    return f"\n  instale o driver com: pip install 'django-auto-rest-project[{extra}]'"


@dataclass(frozen=True)
class DiscoveredModel:
    """Um modelo encontrado na saida do ``inspectdb``."""

    name: str
    db_table: str = ""

    @property
    def snake_name(self) -> str:
        """``AlbumTrack`` -> ``album_track``."""
        return camel_to_snake(self.name)

    @property
    def route(self) -> str:
        """Prefixo de URL do router: ``AlbumTrack`` -> ``album-track``."""
        return self.snake_name.replace("_", "-")

    @property
    def basename(self) -> str:
        """``basename`` usado no ``router.register``."""
        return self.snake_name


def camel_to_snake(name: str) -> str:
    """
    Converte ``CamelCase`` para ``snake_case``.

    O ``inspectdb`` sempre nomeia as classes em CamelCase a partir do nome da
    tabela, entao esta e a unica conversao necessaria.
    """
    intermediate = _CAMEL_BOUNDARY.sub(r"\1_\2", name)
    return _CAMEL_TAIL.sub(r"\1_\2", intermediate).lower()


def configure_django() -> None:
    """
    Configura o Django minimamente, apenas o suficiente para introspeccao.

    Nao ha ``INSTALLED_APPS`` nem ``settings.py``: o ``inspectdb`` so precisa
    de ``DATABASES``. O alias ``default`` fica com o backend dummy porque o
    Django exige que ele exista.
    """
    import django
    from django.conf import settings

    if settings.configured:
        return

    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.dummy"}},
        INSTALLED_APPS=[],
        USE_TZ=True,
    )
    django.setup()


@dataclass(frozen=True)
class SchemaSource:
    """Resultado da introspeccao."""

    models_source: str
    skipped_tables: tuple[str, ...] = ()


@contextmanager
def _registered_database(database: dict[str, str]):
    """
    Registra a conexao sob um alias novo e limpa tudo no final.

    Um alias por chamada mantem a introspeccao reentrante -- varios bancos no
    mesmo processo, util nos testes.
    """
    configure_django()

    from django.conf import settings
    from django.db import connections

    alias = f"robot_rest_{next(_ALIAS_COUNTER)}"
    settings.DATABASES[alias] = dict(database)
    # ``settings`` do ConnectionHandler e um cached_property; sem invalidar,
    # o alias recem-criado nao seria enxergado.
    connections.__dict__.pop("settings", None)
    try:
        yield alias
    finally:
        # A conexao pode nunca ter sido criada (driver ausente, por exemplo).
        # Fechar sem proteger mascara o erro original com um traceback.
        try:
            connections[alias].close()
        except Exception:  # noqa: BLE001 - limpeza best-effort
            pass
        settings.DATABASES.pop(alias, None)
        connections.__dict__.pop("settings", None)


def _introspection_error(database: dict[str, str], exc: Exception) -> IntrospectionError:
    return IntrospectionError(
        f"Nao foi possivel introspectar o banco '{database.get('NAME')}': "
        f"{exc}{driver_hint(database.get('ENGINE', ''), exc)}"
    )


def list_tables(database: dict[str, str]) -> list[str]:
    """
    Lista as tabelas do banco, em ordem alfabetica.

    :raises IntrospectionError: se a conexao falhar.
    """
    with _registered_database(database) as alias:
        from django.db import connections

        try:
            connection = connections[alias]
            with connection.cursor() as cursor:
                return sorted(
                    info.name for info in connection.introspection.get_table_list(cursor) if info.type == "t"
                )
        except Exception as exc:  # noqa: BLE001 - contexto util para o usuario final
            raise _introspection_error(database, exc) from exc


def introspect_schema(database: dict[str, str], include_system_tables: bool = False) -> SchemaSource:
    """
    Introspecta o banco, pulando as tabelas do proprio Django por padrao.

    :param database: dict no formato de ``settings.DATABASES['default']``.
    :param include_system_tables: se ``True``, nao filtra nada.
    :raises IntrospectionError: se a conexao ou a introspeccao falhar.
    """
    tables = list_tables(database)

    skipped: tuple[str, ...] = ()
    if not include_system_tables:
        skipped = tuple(name for name in tables if name.lower() in DJANGO_SYSTEM_TABLES)
        tables = [name for name in tables if name.lower() not in DJANGO_SYSTEM_TABLES]

        # Sem tabelas de usuario, chamar o inspectdb sem argumentos traria o
        # banco inteiro de volta -- exatamente o que acabou de ser filtrado.
        if not tables:
            return SchemaSource(models_source=EMPTY_MODELS_SOURCE, skipped_tables=skipped)

    return SchemaSource(models_source=run_inspectdb(database, tables=tables), skipped_tables=skipped)


def run_inspectdb(database: dict[str, str], tables: list[str] | None = None) -> str:
    """
    Roda o ``inspectdb`` contra o banco informado e devolve o models.py.

    :param database: dict no formato de ``settings.DATABASES['default']``.
    :param tables: se informado, limita a introspeccao a essas tabelas.
    :return: o codigo-fonte do ``models.py``.
    :raises IntrospectionError: se a conexao ou a introspeccao falhar.
    """
    from django.core.management import call_command

    buffer = io.StringIO()
    with _registered_database(database) as alias:
        try:
            call_command("inspectdb", *(tables or []), database=alias, stdout=buffer)
        except Exception as exc:  # noqa: BLE001 - contexto util para o usuario final
            raise _introspection_error(database, exc) from exc

    return buffer.getvalue()


_MANAGED_FALSE = re.compile(r"^(?P<indent>\s*)managed = False\s*$", re.MULTILINE)


def set_managed(models_source: str, managed: bool) -> str:
    """
    Alterna o ``Meta.managed`` dos modelos gerados pelo inspectdb.

    O inspectdb sempre emite ``managed = False``, o que faz o Django ignorar
    essas tabelas em makemigrations/migrate -- seguro para um banco que ja
    existe. Com ``managed=True`` o Django passa a considerar o schema dele.

    :param models_source: codigo-fonte do models.py.
    :param managed: se ``False``, devolve a fonte intacta.
    """
    if not managed:
        return models_source
    return _MANAGED_FALSE.sub(lambda match: f"{match.group('indent')}managed = True", models_source)


def _is_model_base(node: ast.expr) -> bool:
    """Reconhece ``models.Model`` e ``Model`` como classe base."""
    if isinstance(node, ast.Attribute):
        return node.attr == "Model"
    return isinstance(node, ast.Name) and node.id == "Model"


def _meta_db_table(node: ast.ClassDef) -> str:
    """Extrai ``Meta.db_table`` da classe, quando presente."""
    for item in node.body:
        if not (isinstance(item, ast.ClassDef) and item.name == "Meta"):
            continue
        for statement in item.body:
            if not isinstance(statement, ast.Assign):
                continue
            for target in statement.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == "db_table"
                    and isinstance(statement.value, ast.Constant)
                    and isinstance(statement.value.value, str)
                ):
                    return statement.value.value
    return ""


def discover_models(models_source: str) -> list[DiscoveredModel]:
    """
    Extrai os modelos de um ``models.py`` sem importa-lo.

    Usar ``ast`` em vez de import evita depender do Django estar configurado
    e de o modulo ser importavel -- o ``inspectdb`` pode gerar codigo que nao
    carrega (por exemplo, tabelas sem chave primaria).

    :param models_source: codigo-fonte do models.py.
    :return: modelos em ordem alfabetica.
    :raises IntrospectionError: se o codigo nao puder ser lido.
    """
    try:
        tree = ast.parse(models_source)
    except SyntaxError as exc:
        raise IntrospectionError(f"O models.py gerado pelo inspectdb nao pode ser lido: {exc}") from exc

    models = [
        DiscoveredModel(name=node.name, db_table=_meta_db_table(node))
        for node in tree.body
        if isinstance(node, ast.ClassDef) and any(_is_model_base(base) for base in node.bases)
    ]
    return sorted(models, key=lambda model: model.name)
