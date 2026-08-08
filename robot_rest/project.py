"""
Pipeline de geracao do projeto.

Diferente da versao antiga, nada aqui instala pacotes no ambiente do usuario
nem pede input no meio do caminho: o resultado e um diretorio de projeto com
um ``requirements.txt`` proprio, que o usuario instala onde quiser.
"""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .config import ProjectConfig
from .introspect import DiscoveredModel, discover_models, run_inspectdb
from .render import build_environment, render_to

#: Templates do projeto -> caminho de saida, relativo a raiz do projeto.
#: ``{package}`` e substituido pelo nome do pacote do projeto.
PROJECT_TEMPLATES = {
    "project/urls.py.j2": "{package}/urls.py",
    "project/settings/__init__.py.j2": "{package}/settings/__init__.py",
    "project/settings/defaults.py.j2": "{package}/settings/defaults.py",
    "project/settings/dev.py.j2": "{package}/settings/dev.py",
    "project/settings/production.py.j2": "{package}/settings/production.py",
    "project/settings/tests.py.j2": "{package}/settings/tests.py",
    "project/tests/__init__.py.j2": "{package}/tests/__init__.py",
    "project/tests/settingstest.py.j2": "{package}/tests/settingstest.py",
    "project/tests/test_rest_api.py.j2": "{package}/tests/test_rest_api.py",
    "project/requirements.txt.j2": "requirements.txt",
}

#: Templates do app ``core``, renderizados a partir dos modelos descobertos.
CORE_TEMPLATES = {
    "core/serializers.py.j2": "core/serializers.py",
    "core/views.py.j2": "core/views.py",
    "core/urls.py.j2": "core/urls.py",
    "core/admin.py.j2": "core/admin.py",
}

#: Nome do app que recebe o codigo gerado.
CORE_APP = "core"


class ProjectExistsError(FileExistsError):
    """O diretorio de destino ja existe."""


@dataclass(frozen=True)
class GenerationResult:
    """Resumo do que foi gerado, para a CLI relatar ao usuario."""

    project_dir: Path
    models: list[DiscoveredModel]

    @property
    def model_count(self) -> int:
        return len(self.models)


def _run_django_command(name: str, *args, **options) -> None:
    """Executa um management command do Django em processo."""
    from django.core.management import call_command

    call_command(name, *args, **options)


def scaffold(project_dir: Path, project_name: str) -> None:
    """
    Cria o esqueleto do projeto e do app ``core`` usando o proprio Django.

    Delegar para ``startproject``/``startapp`` mantem manage.py, wsgi.py e
    asgi.py alinhados com a versao do Django instalada.
    """
    from .introspect import configure_django

    configure_django()

    project_dir.mkdir(parents=True)
    _run_django_command("startproject", project_name, str(project_dir), verbosity=0)

    app_dir = project_dir / CORE_APP
    app_dir.mkdir()
    _run_django_command("startapp", CORE_APP, str(app_dir), verbosity=0)

    # O startproject grava um settings.py que sera substituido pelo pacote
    # settings/ renderizado a seguir. Deixar os dois quebra o import.
    (project_dir / project_name / "settings.py").unlink(missing_ok=True)


def write_models(project_dir: Path, models_source: str) -> None:
    """
    Grava o ``models.py`` vindo do inspectdb dentro do app ``core``.
    """
    (project_dir / CORE_APP / "models.py").write_text(models_source, encoding="utf-8")


def render_project(project_dir: Path, config: ProjectConfig, models: list[DiscoveredModel]) -> None:
    """
    Renderiza todos os templates -- projeto e app ``core``.
    """
    environment = build_environment()
    context = config.as_template_context()
    context["models"] = models

    for template_name, output in {**PROJECT_TEMPLATES, **CORE_TEMPLATES}.items():
        destination = project_dir / output.format(package=config.project_name)
        render_to(template_name, destination, context, environment)


def generate(config: ProjectConfig, destination: Path | None = None) -> GenerationResult:
    """
    Gera o projeto completo a partir do banco descrito em ``config``.

    Em caso de erro, remove o diretorio parcialmente criado -- a versao antiga
    deixava um projeto pela metade no disco.

    :param config: configuracao validada do projeto.
    :param destination: diretorio pai; por padrao o diretorio atual.
    :raises ProjectExistsError: se o destino ja existir.
    """
    parent = Path(destination or Path.cwd())
    project_dir = parent / config.project_name

    if project_dir.exists():
        raise ProjectExistsError(
            f"'{project_dir}' ja existe. Escolha outro nome de projeto ou remova o diretorio."
        )

    # Introspecta antes de criar qualquer arquivo: erro de conexao, senha ou
    # driver e o caso comum, e nao deve deixar nada no disco.
    models_source = run_inspectdb(config.database.as_django_dict())
    models = discover_models(models_source)

    # O projeto e montado em um diretorio temporario e so depois movido para
    # o destino. Duas razoes:
    #   1. Um diretorio vazio no destino conta como namespace package, e o
    #      startproject recusa o nome ("conflicts with an existing module")
    #      justamente no caso mais comum -- gerar no diretorio atual.
    #   2. O destino so passa a existir com o projeto ja completo; qualquer
    #      falha no meio some junto com o diretorio temporario.
    with tempfile.TemporaryDirectory(prefix="robot_rest_") as staging_root:
        staging = Path(staging_root) / config.project_name

        scaffold(staging, config.project_name)
        write_models(staging, models_source)
        render_project(staging, config, models)

        if project_dir.exists():
            raise ProjectExistsError(f"'{project_dir}' foi criado durante a geracao. Abortando.")

        parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(staging), str(project_dir))

    return GenerationResult(project_dir=project_dir, models=models)
