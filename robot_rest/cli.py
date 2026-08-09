"""Interface de linha de comando do robot_rest."""

from __future__ import annotations

import getpass
import os
import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path

from . import __version__
from .config import (
    ENGINE_ALIASES,
    SQLITE_ENGINE,
    ConfigError,
    DatabaseConfig,
    ProjectConfig,
    needs_credentials,
    resolve_engine,
    validate_database_config,
)
from .introspect import IntrospectionError
from .project import ProjectExistsError, generate

#: Variavel de ambiente consultada antes de perguntar a senha.
PASSWORD_ENV_VAR = "ROBOT_REST_DB_PASSWORD"

EPILOG = """\
exemplos:
  # MySQL, senha perguntada interativamente (recomendado)
  robot_rest -ip 127.0.0.1 -user appuser -database appdb -project myapi

  # PostgreSQL
  robot_rest -engine postgres -ip 127.0.0.1 -user appuser \\
      -database appdb -project myapi

  # SQLite: so o caminho do arquivo, sem host, usuario ou senha
  robot_rest -engine sqlite -database ./app.sqlite3 -project myapi

  # senha via ambiente, para uso em scripts
  ROBOT_REST_DB_PASSWORD=... robot_rest -ip 127.0.0.1 -user appuser \\
      -database appdb -project myapi
"""


def build_parser() -> ArgumentParser:
    """
    Constroi o parser de linha de comando.
    """
    parser = ArgumentParser(
        prog="robot_rest",
        description="Gera um projeto Django + Django REST Framework a partir de um banco existente.",
        epilog=EPILOG,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"robot_rest {__version__}")
    parser.add_argument("-vv", "--verbose", action="store_true", help="Increase verbosity.")
    parser.add_argument(
        "-engine",
        dest="engine",
        default="mysql",
        choices=sorted(ENGINE_ALIASES),
        help="Database engine (default: mysql)",
    )
    parser.add_argument(
        "-ip",
        dest="database_host",
        default="",
        help="Host address of the database. Required except for sqlite.",
    )
    parser.add_argument(
        "-user",
        dest="database_user",
        default="",
        help="Username that have access database. Required except for sqlite.",
    )
    parser.add_argument(
        "-database",
        required=True,
        dest="database_name",
        help="The name of the database, or the file path for sqlite",
    )
    parser.add_argument("-project", required=True, dest="project_name", help="The name of the project.")
    parser.add_argument("-port", dest="database_port", default="", help="Database port (default: per engine)")
    parser.add_argument(
        "--all-tables",
        action="store_true",
        dest="include_system_tables",
        help=(
            "Also introspect Django's own tables (auth_user, django_session, ...). "
            "They are skipped by default: they would collide with Django's models and "
            "expose the auth tables as REST routes."
        ),
    )
    parser.add_argument(
        "--no-auth",
        action="store_false",
        dest="auth_enabled",
        help=("Skip the accounts app (sign up, login, password reset). It is included by default."),
    )
    parser.add_argument(
        "--managed",
        action="store_true",
        help=(
            "Mark the generated models as managed = True, so Django owns their schema. "
            "By default inspectdb models are unmanaged and migrate never touches those tables."
        ),
    )
    parser.add_argument(
        "-password",
        dest="database_password",
        default=None,
        help=(
            f"Password to access the database. Prefer ${PASSWORD_ENV_VAR} or the interactive prompt: "
            "a password given here is visible in the shell history and the process list."
        ),
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        dest="output_dir",
        default=None,
        help="Where to create the project (default: current directory)",
    )
    return parser


def resolve_password(supplied: str | None, environ: dict | None = None, prompt=getpass.getpass) -> str:
    """
    Resolve a senha do banco na ordem: argumento, ambiente, prompt.

    Passar a senha em ``-password`` deixa rastro no historico do shell e na
    tabela de processos, por isso ela deixou de ser obrigatoria.

    :param supplied: valor vindo de ``-password``, se houver.
    :param environ: mapeamento de ambiente (default: ``os.environ``).
    :param prompt: callable usado para perguntar; injetavel nos testes.
    """
    if supplied is not None:
        return supplied

    env = os.environ if environ is None else environ
    from_env = env.get(PASSWORD_ENV_VAR)
    if from_env is not None:
        return from_env

    return prompt("Senha do banco de dados: ")


def build_config(args, password: str) -> ProjectConfig:
    """
    Converte os argumentos da CLI em :class:`ProjectConfig`.

    :raises ConfigError: se faltar algo obrigatorio para a engine escolhida.
    """
    engine = resolve_engine(args.engine)
    name = args.database_name

    # O projeto gerado roda a partir de outro diretorio, entao um caminho
    # relativo de SQLite precisa virar absoluto antes de ir para o .env.
    if engine == SQLITE_ENGINE and name:
        name = str(Path(name).expanduser().resolve())

    database = validate_database_config(
        DatabaseConfig(
            name=name,
            user=args.database_user,
            password=password,
            host=args.database_host,
            port=args.database_port,
            engine=engine,
        )
    )
    return ProjectConfig(
        project_name=args.project_name,
        database=database,
        auth_enabled=args.auth_enabled,
    )


def report(result, stream=sys.stdout) -> None:
    """
    Mostra o resumo e os proximos passos.

    O robot nao instala mais nada no ambiente do usuario, entao a instalacao
    das dependencias vira uma instrucao explicita.
    """
    project_dir = result.project_dir
    print(f"\nProjeto gerado em {project_dir}", file=stream)
    print(f"{result.model_count} modelo(s) mapeado(s) a partir do banco.", file=stream)

    if result.model_count == 0:
        print(
            "Nenhuma tabela foi encontrada. Confira se o usuario tem permissao de leitura no banco.",
            file=stream,
        )

    if result.skipped_tables:
        # Nada de corte silencioso: o usuario precisa saber o que ficou de fora.
        print(
            f"\nTabelas do proprio Django ignoradas ({len(result.skipped_tables)}): "
            f"{', '.join(result.skipped_tables)}.\n"
            "Use --all-tables se quiser mapea-las mesmo assim.",
            file=stream,
        )

    if result.dropped_models:
        print(
            f"\nModelos descartados por apontarem para tabelas filtradas "
            f"({len(result.dropped_models)}): {', '.join(result.dropped_models)}.",
            file=stream,
        )

    if result.managed:
        print(
            "\nAtencao: os modelos foram marcados como managed = True. O Django passa a\n"
            "gerenciar o schema dessas tabelas, entao makemigrations/migrate podem alterar\n"
            "ou apagar dados do banco existente. Revise as migracoes antes de aplicar.",
            file=stream,
        )

    print("\nProximos passos:", file=stream)
    print(f"  cd {project_dir.name}", file=stream)
    print("  python -m venv .venv && source .venv/bin/activate", file=stream)
    print("  pip install -r requirements.txt", file=stream)
    print("  python manage.py migrate", file=stream)
    print("  python manage.py createsuperuser", file=stream)
    print("  python manage.py runserver", file=stream)

    if result.auth_enabled:
        print("\nContas (cadastro, login e senha) em /v1/auth/:", file=stream)
        print("  POST /v1/auth/registration/           cria a conta", file=stream)
        print("  POST /v1/auth/login/                  devolve o token", file=stream)
        print("  POST /v1/auth/logout/                 invalida o token", file=stream)
        print("  GET  /v1/auth/user/                   dados da conta", file=stream)
        print("  POST /v1/auth/password/change/        troca a senha", file=stream)
        print("  POST /v1/auth/password/reset/         envia o e-mail", file=stream)
        print("  POST /v1/auth/password/reset/confirm/ aplica a nova senha", file=stream)
        print("Em desenvolvimento os e-mails saem no console do runserver.", file=stream)

    print("\nDepois de subir o servidor:", file=stream)
    print("  http://127.0.0.1:8000/v1/docs/    documentacao (Swagger UI)", file=stream)
    print("  http://127.0.0.1:8000/v1/schema/  schema OpenAPI", file=stream)
    print("  http://127.0.0.1:8000/admin/      admin do Django", file=stream)
    print("  POST /v1/token-auth/ com usuario e senha devolve o token da API.", file=stream)

    print(f"\nA conexao com o banco e a SECRET_KEY ficaram em {project_dir.name}/.env", file=stream)
    print("(modo 600, e ja listado no .gitignore -- nao versione esse arquivo).", file=stream)
    print(
        f"Testes: python manage.py test --settings={project_dir.name}.settings.tests",
        file=stream,
    )


def main(argv: list[str] | None = None) -> int:
    """
    Ponto de entrada da CLI.

    :return: codigo de saida (0 em caso de sucesso).
    """
    args = build_parser().parse_args(argv)

    try:
        engine = resolve_engine(args.engine)
        # SQLite e um arquivo local: nao faz sentido pedir senha.
        password = resolve_password(args.database_password) if needs_credentials(engine) else ""
        config = build_config(args, password)
        output_dir = Path(args.output_dir) if args.output_dir else None
        result = generate(
            config,
            destination=output_dir,
            managed=args.managed,
            include_system_tables=args.include_system_tables,
        )
    except (ConfigError, ProjectExistsError, IntrospectionError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\ncancelado.", file=sys.stderr)
        return 130

    report(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
