"""
Trava o contrato de empacotamento dos templates.

Um template novo exige tres edicoes coordenadas: criar o ``.tpl``, listar o
caminho em ``TEMPLATE_PATHS`` e declarar o glob em ``package-data``. Esquecer
a terceira faz o arquivo sumir apenas na instalacao via pip -- falha que so
aparece para o usuario final. Estes testes quebram antes disso.
"""

import fnmatch
import re
import sys
from pathlib import Path

import pytest

from robot_rest.robot_rest import PACKAGE_DIR, PLACEHOLDERS, TEMPLATE_PATHS

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - Python 3.10
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER_RE = re.compile(r"@[A-Za-z_]+@")

#: Templates copiados diretamente, sem passar por TEMPLATE_PATHS.
STANDALONE_TEMPLATES = ("urls.tpl",)


def package_data_globs():
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        config = tomllib.load(handle)
    return config["tool"]["setuptools"]["package-data"]["robot_rest"]


def all_templates():
    return sorted(PACKAGE_DIR.rglob("*.tpl"))


@pytest.mark.parametrize("path", TEMPLATE_PATHS)
def test_template_path_resolves_to_a_real_file(path):
    assert (PACKAGE_DIR / (path.lstrip("/") + ".tpl")).is_file()


def test_template_paths_have_no_leading_slash():
    assert [p for p in TEMPLATE_PATHS if p.startswith("/")] == []


def test_every_template_on_disk_is_rendered_or_standalone():
    rendered = {p.lstrip("/") + ".tpl" for p in TEMPLATE_PATHS}
    known = rendered | set(STANDALONE_TEMPLATES)
    on_disk = {str(p.relative_to(PACKAGE_DIR)) for p in all_templates()}
    assert on_disk == known


@pytest.mark.parametrize("template", all_templates(), ids=lambda p: p.name)
def test_template_is_covered_by_package_data(template):
    relative = str(template.relative_to(PACKAGE_DIR))
    globs = package_data_globs()
    assert any(fnmatch.fnmatch(relative, pattern) for pattern in globs), (
        f"{relative} nao esta coberto por package-data em pyproject.toml"
    )


def test_runtime_requirements_are_covered_by_package_data():
    globs = package_data_globs()
    assert any(fnmatch.fnmatch("requirements.txt", pattern) for pattern in globs)


@pytest.mark.parametrize("template", all_templates(), ids=lambda p: p.name)
def test_template_uses_only_known_placeholders(template):
    found = set(PLACEHOLDER_RE.findall(template.read_text(encoding="utf-8")))
    unknown = found - set(PLACEHOLDERS)
    assert not unknown, f"{template.name} usa placeholder desconhecido: {unknown}"


@pytest.mark.parametrize("template", all_templates(), ids=lambda p: p.name)
def test_template_has_no_python2_implicit_relative_import(template):
    text = template.read_text(encoding="utf-8")
    offenders = re.findall(r"^from (defaults|dev|production|tests) import", text, flags=re.MULTILINE)
    assert offenders == [], f"{template.name} usa import relativo implicito (Python 2): {offenders}"
