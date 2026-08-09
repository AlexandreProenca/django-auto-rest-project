"""
Trava o contrato de empacotamento dos templates.

Um template novo precisa existir sob ``robot_rest/templates/`` *e* cair em um
glob de ``package-data``. Esquecer o segundo passo faz o arquivo sumir apenas
na instalacao via pip -- falha que so aparece para o usuario final.
"""

import fnmatch
import re
import sys
from pathlib import Path

import pytest

from robot_rest.project import CORE_TEMPLATES, PROJECT_TEMPLATES
from robot_rest.render import TEMPLATES_DIR, iter_template_names

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - Python 3.10
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Sintaxe do gerador antigo. Nao pode reaparecer nos templates.
LEGACY_PLACEHOLDER_RE = re.compile(r"@[A-Za-z_]+@")


def package_data_globs():
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        config = tomllib.load(handle)
    return config["tool"]["setuptools"]["package-data"]["robot_rest"]


TEMPLATE_NAMES = iter_template_names()


def test_templates_are_present():
    assert TEMPLATE_NAMES, "nenhum template encontrado em robot_rest/templates/"


@pytest.mark.parametrize("name", TEMPLATE_NAMES)
def test_template_is_covered_by_package_data(name):
    relative = f"templates/{name}"
    globs = package_data_globs()
    matched = any(fnmatch.fnmatch(relative, pattern) or Path(relative).match(pattern) for pattern in globs)
    assert matched, f"{relative} nao esta coberto por package-data em pyproject.toml"


@pytest.mark.parametrize("template_name", sorted({**PROJECT_TEMPLATES, **CORE_TEMPLATES}))
def test_referenced_template_exists(template_name):
    assert (TEMPLATES_DIR / template_name).is_file()


def test_every_template_on_disk_is_referenced():
    referenced = set({**PROJECT_TEMPLATES, **CORE_TEMPLATES})
    assert set(TEMPLATE_NAMES) == referenced


@pytest.mark.parametrize("name", TEMPLATE_NAMES)
def test_no_legacy_placeholder_syntax(name):
    text = (TEMPLATES_DIR / name).read_text(encoding="utf-8")
    found = LEGACY_PLACEHOLDER_RE.findall(text)
    assert found == [], f"{name} ainda usa a sintaxe antiga: {found}"


@pytest.mark.parametrize("name", TEMPLATE_NAMES)
def test_no_python2_implicit_relative_import(name):
    text = (TEMPLATES_DIR / name).read_text(encoding="utf-8")
    offenders = re.findall(r"^from (defaults|dev|production|tests) import", text, flags=re.MULTILINE)
    assert offenders == [], f"{name} usa import relativo implicito (Python 2): {offenders}"


def test_console_script_points_at_the_cli():
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        config = tomllib.load(handle)
    assert config["project"]["scripts"]["robot_rest"] == "robot_rest.cli:main"


def test_version_is_consistent_across_files():
    # A versao vive em robot_rest/__init__.py; o bumpversion guarda uma copia.
    # Se as duas divergirem, o proximo bump volta para a versao errada.
    import robot_rest

    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        config = tomllib.load(handle)
    assert config["tool"]["bumpversion"]["current_version"] == robot_rest.__version__


def test_changelog_mentions_the_current_version():
    import robot_rest

    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"[{robot_rest.__version__}]" in changelog


def test_readme_documents_every_cli_option():
    # O README ja ficou desatualizado em relacao a CLI mais de uma vez.
    from robot_rest.cli import build_parser

    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    documented = []
    for action in build_parser()._actions:
        flags = [flag for flag in action.option_strings if flag.startswith("-")]
        if flags and not any(flag in readme for flag in flags):
            documented.append(flags[0])
    assert documented == [], f"opcoes ausentes do README: {documented}"


def test_drf_gen_is_not_a_dependency():
    # A dependencia morta que o Phase 1 removeu.
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        config = tomllib.load(handle)
    declared = " ".join(config["project"]["dependencies"]).lower()
    assert "drf-file-generator" not in declared
