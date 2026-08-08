"""Configuracao imutavel usada por todo o pipeline de geracao."""

from __future__ import annotations

import keyword
import string
from dataclasses import dataclass, field
from random import SystemRandom

#: Tamanho da SECRET_KEY gerada para o projeto.
SECRET_KEY_LENGTH = 50

#: Engines suportadas, mapeadas para a porta padrao de cada banco.
#: Hoje a CLI so expoe MySQL; as demais existem para os testes e para
#: preparar o suporte multi-banco.
DEFAULT_PORTS = {
    "django.db.backends.mysql": "3306",
    "django.db.backends.postgresql": "5432",
    "django.db.backends.sqlite3": "",
}

MYSQL_ENGINE = "django.db.backends.mysql"


class ConfigError(ValueError):
    """Configuracao invalida informada pelo usuario."""


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
