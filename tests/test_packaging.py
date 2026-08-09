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

from robot_rest.project import AUTH_TEMPLATES, CORE_TEMPLATES, PROJECT_TEMPLATES
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


@pytest.mark.parametrize("template_name", sorted({**PROJECT_TEMPLATES, **CORE_TEMPLATES, **AUTH_TEMPLATES}))
def test_referenced_template_exists(template_name):
    assert (TEMPLATES_DIR / template_name).is_file()


def test_every_template_on_disk_is_referenced():
    referenced = set({**PROJECT_TEMPLATES, **CORE_TEMPLATES, **AUTH_TEMPLATES})
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


#: Fixtures SQL usadas pelos containers.
INITDB_DIR = REPO_ROOT / "docker" / "initdb"


@pytest.mark.parametrize("fixture", sorted(p.name for p in INITDB_DIR.glob("*.sql")))
def test_initdb_fixture_is_mounted_by_compose(fixture):
    # Um arquivo renomeado e esquecido aqui vira um banco vazio, e o erro so
    # aparece quando alguem tenta usar o container.
    compose = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert f"docker/initdb/{fixture}" in compose


def test_demo_fixture_creates_the_documented_tables():
    # O README promete estas tabelas ao leitor que subir o demo.
    sql = (INITDB_DIR / "demo-mysql.sql").read_text(encoding="utf-8")
    expected = {
        "category",
        "customer",
        "customer_address",
        "customer_order",
        "order_item",
        "product",
        "product_tag",
        "tag",
    }
    created = set(re.findall(r"CREATE TABLE (\w+)", sql))
    assert created == expected


def test_demo_fixture_has_enough_rows_to_paginate():
    # O valor do demo esta em ver a paginacao funcionando: PAGE_SIZE e 10.
    sql = (INITDB_DIR / "demo-mysql.sql").read_text(encoding="utf-8")
    products = sql.split("INSERT INTO product (", 1)[1].split(";", 1)[0]
    assert products.count("'SKU-") > 10


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


#: Pacotes que o projeto deixou de usar. Se voltarem ao README e porque a
#: documentacao ficou descrevendo uma versao anterior.
ABANDONED_PACKAGES = [
    "django-drf-file-generator",
    "django-rest-swagger",
    "django-rest-auth",
    "django-jet",
    "MySQL-python",
    "dj-rest-auth",
]


@pytest.mark.parametrize("package", ABANDONED_PACKAGES)
def test_readme_does_not_mention_dropped_packages(package):
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert package.lower() not in readme.lower()


def test_readme_documents_the_generated_dependencies():
    # O README lista o que o projeto gerado instala; a lista real vive no
    # template. Ja divergiu antes.
    from robot_rest.config import DatabaseConfig
    from robot_rest.render import render

    rendered = render(
        "project/requirements.txt.j2",
        {
            "project_name": "p",
            "secret_key": "k",
            "database": DatabaseConfig(name="d").as_django_dict(),
            "models": [],
            "auth_enabled": True,
        },
    )
    declared = [
        line.split(">=")[0].split("<")[0].split("[")[0].strip()
        for line in rendered.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8").lower()
    # 'djangorestframework' aparece escrito por extenso na prosa.
    aliases = {"djangorestframework": "django rest framework"}
    missing = [d for d in declared if aliases.get(d, d).lower() not in readme]
    assert missing == [], f"dependencias do projeto gerado ausentes do README: {missing}"


def test_readme_uses_the_current_activation_url():
    # A rota de ativacao nao recebe a chave no caminho desde a 5.x; o README
    # documentava a forma antiga depois da migracao.
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "/accounts/activate/<key>" not in readme
    if "accounts/activate/" in readme:
        assert "activation_key=" in readme


def test_drf_gen_is_not_a_dependency():
    # A dependencia morta que o Phase 1 removeu.
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        config = tomllib.load(handle)
    declared = " ".join(config["project"]["dependencies"]).lower()
    assert "drf-file-generator" not in declared
