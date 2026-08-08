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
from dataclasses import dataclass

_ALIAS_COUNTER = itertools.count()

_CAMEL_BOUNDARY = re.compile(r"(.)([A-Z][a-z]+)")
_CAMEL_TAIL = re.compile(r"([a-z0-9])([A-Z])")


#: Extra do pacote que instala o driver de cada engine.
DRIVER_EXTRAS = {
    "django.db.backends.mysql": "mysql",
    "django.db.backends.postgresql": "postgres",
}


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


def run_inspectdb(database: dict[str, str], tables: list[str] | None = None) -> str:
    """
    Roda o ``inspectdb`` contra o banco informado e devolve o models.py.

    Registra a conexao sob um alias novo a cada chamada, o que mantem a
    funcao reentrante -- varios bancos no mesmo processo, util nos testes.

    :param database: dict no formato de ``settings.DATABASES['default']``.
    :param tables: se informado, limita a introspeccao a essas tabelas.
    :return: o codigo-fonte do ``models.py``.
    :raises IntrospectionError: se a conexao ou a introspeccao falhar.
    """
    configure_django()

    from django.conf import settings
    from django.core.management import call_command
    from django.db import connections

    alias = f"robot_rest_{next(_ALIAS_COUNTER)}"
    settings.DATABASES[alias] = dict(database)
    # ``settings`` do ConnectionHandler e um cached_property; sem invalidar,
    # o alias recem-criado nao seria enxergado.
    connections.__dict__.pop("settings", None)

    buffer = io.StringIO()
    try:
        call_command("inspectdb", *(tables or []), database=alias, stdout=buffer)
    except Exception as exc:  # noqa: BLE001 - contexto util para o usuario final
        raise IntrospectionError(
            f"Nao foi possivel introspectar o banco '{database.get('NAME')}': "
            f"{exc}{driver_hint(database.get('ENGINE', ''), exc)}"
        ) from exc
    finally:
        # A conexao pode nunca ter sido criada (driver ausente, por exemplo).
        # Fechar sem proteger mascara o erro original com um traceback.
        try:
            connections[alias].close()
        except Exception:  # noqa: BLE001 - limpeza best-effort
            pass
        settings.DATABASES.pop(alias, None)
        connections.__dict__.pop("settings", None)

    return buffer.getvalue()


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
