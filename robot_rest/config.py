"""Configuracao imutavel usada por todo o pipeline de geracao."""

from __future__ import annotations

import keyword
import string
from dataclasses import dataclass, field
from random import SystemRandom

#: Tamanho da SECRET_KEY gerada para o projeto.
SECRET_KEY_LENGTH = 50

#: Engines suportadas, mapeadas para a porta padrao de cada banco.
DEFAULT_PORTS = {
    "django.db.backends.mysql": "3306",
    "django.db.backends.postgresql": "5432",
    "django.db.backends.sqlite3": "",
}

MYSQL_ENGINE = "django.db.backends.mysql"
POSTGRES_ENGINE = "django.db.backends.postgresql"
SQLITE_ENGINE = "django.db.backends.sqlite3"

#: Nomes aceitos em ``-engine`` -> engine do Django.
ENGINE_ALIASES = {
    "mysql": MYSQL_ENGINE,
    "mariadb": MYSQL_ENGINE,
    "postgres": POSTGRES_ENGINE,
    "postgresql": POSTGRES_ENGINE,
    "sqlite": SQLITE_ENGINE,
    "sqlite3": SQLITE_ENGINE,
}

#: Engines que rodam em um servidor e portanto exigem host e usuario.
#: O SQLite e um arquivo local, entao nao pede nem host, nem usuario, nem senha.
SERVER_ENGINES = frozenset({MYSQL_ENGINE, POSTGRES_ENGINE})


class ConfigError(ValueError):
    """Configuracao invalida informada pelo usuario."""


def resolve_engine(name: str) -> str:
    """
    Converte o nome amigavel da CLI na engine do Django.

    :raises ConfigError: se a engine nao for suportada.
    """
    try:
        return ENGINE_ALIASES[name.strip().lower()]
    except KeyError:
        supported = ", ".join(sorted(set(ENGINE_ALIASES)))
        raise ConfigError(f"Engine '{name}' nao suportada. Use uma destas: {supported}.") from None


def needs_credentials(engine: str) -> bool:
    """Indica se a engine exige host, usuario e senha."""
    return engine in SERVER_ENGINES


def generate_secret_key(length: int = SECRET_KEY_LENGTH) -> str:
    """
    Gera uma SECRET_KEY aleatoria usando o gerador criptografico do sistema.

    :param length: numero de caracteres da chave.
    """
    alphabet = string.ascii_letters + string.digits
    rand = SystemRandom()
    return "".join(rand.choice(alphabet) for _ in range(length))


def validate_project_name(name: str) -> str:
    """
    Valida o nome do projeto antes de criar qualquer arquivo.

    O nome vira um pacote Python, entao precisa ser um identificador valido.
    Falhar aqui evita deixar um diretorio pela metade no disco.

    :raises ConfigError: se o nome nao servir como pacote.
    """
    if not name:
        raise ConfigError("O nome do projeto nao pode ser vazio.")
    if not name.isidentifier():
        raise ConfigError(
            f"'{name}' nao e um nome de projeto valido: use apenas letras, numeros e underscore, "
            "sem comecar com numero."
        )
    if keyword.iskeyword(name):
        raise ConfigError(f"'{name}' e uma palavra reservada do Python e nao pode nomear o projeto.")
    return name


def validate_database_config(database: DatabaseConfig) -> DatabaseConfig:
    """
    Valida a conexao antes de tentar usa-la.

    Fica aqui, e nao no ``__post_init__``, porque so vale para o que o
    usuario digita na CLI -- o codigo interno e os testes montam conexoes
    parciais de proposito.

    :raises ConfigError: se faltar algo obrigatorio para a engine escolhida.
    """
    if not database.name:
        alvo = "o caminho do arquivo" if database.engine == SQLITE_ENGINE else "o nome do banco"
        raise ConfigError(f"Informe {alvo} em -database.")

    if needs_credentials(database.engine):
        missing = []
        if not database.host:
            missing.append("-ip")
        if not database.user:
            missing.append("-user")
        if missing:
            raise ConfigError(
                f"{' e '.join(missing)} {'sao' if len(missing) > 1 else 'e'} obrigatorio(s) "
                f"para a engine '{database.engine.rsplit('.', 1)[-1]}'."
            )

    return database


@dataclass(frozen=True)
class DatabaseConfig:
    """Dados de conexao com o banco que sera introspectado."""

    name: str
    user: str = ""
    password: str = ""
    host: str = ""
    port: str = ""
    engine: str = MYSQL_ENGINE

    def as_django_dict(self) -> dict[str, str]:
        """
        Converte para o formato aceito em ``settings.DATABASES``.
        """
        return {
            "ENGINE": self.engine,
            "NAME": self.name,
            "USER": self.user,
            "PASSWORD": self.password,
            "HOST": self.host,
            "PORT": self.port or DEFAULT_PORTS.get(self.engine, ""),
        }


@dataclass(frozen=True)
class ProjectConfig:
    """Tudo que os templates precisam para gerar um projeto."""

    project_name: str
    database: DatabaseConfig
    secret_key: str = field(default_factory=generate_secret_key)

    def __post_init__(self) -> None:
        validate_project_name(self.project_name)

    def as_template_context(self) -> dict[str, object]:
        """
        Contexto passado ao Jinja2. Os modelos entram depois, no codegen.
        """
        return {
            "project_name": self.project_name,
            "secret_key": self.secret_key,
            "database": self.database.as_django_dict(),
        }
