# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`django-auto-rest-project` is a **code generator**, not a Django app. It ships a single console script (`robot_rest`) that points at an existing MySQL database and scaffolds a complete Django 1.8 + Django REST Framework project from that schema.

The distribution name on PyPI is `django-auto-rest-project`; the Python package is `robot_rest`.

```bash
robot_rest -ip 127.0.0.1 -user someuser -database somedb -project myproject -password secret
```

All five flags are required. The command is destructive-ish in the CWD: it creates `./<project_name>/`, pip-installs into the active environment, and runs `createsuperuser` interactively. Never run it to "test a change" outside a throwaway virtualenv + directory.

## Commands

Packaging is `pyproject.toml` + setuptools. The package itself has **no runtime dependencies** — it shells out to `django-admin`/`drf_gen` — so the dev environment is cheap.

```bash
pip install -e ".[dev]"
```

```bash
python -m pytest
```

Single test:

```bash
python -m pytest tests/test_robot.py::TestSubstituteLine::test_replaces_every_placeholder_on_the_same_line
```

Lint and format (ruff is the only linter; CI runs both):

```bash
ruff check . && ruff format --check .
```

Build and verify a distribution:

```bash
python -m build && python -m twine check dist/*
```

Version bump — single source of truth is `__version__` in [robot_rest/__init__.py](robot_rest/__init__.py); `[tool.bumpversion]` in pyproject also commits and tags:

```bash
bump-my-version bump patch
```

CI is [.github/workflows/ci.yml](.github/workflows/ci.yml): lint, a pytest matrix on Python 3.10–3.13, a build job that asserts every `.tpl` survives into the wheel, and a tag-triggered PyPI publish via trusted publishing (no secrets — needs the publisher configured on pypi.org).

## Architecture

Orchestration lives in `main()` in [robot_rest/robot_rest.py](robot_rest/robot_rest.py) — a linear pipeline of shell-outs with **no rollback if a step fails**. The pure parts (template rendering, secret generation, context building) are module-level functions and are the only things under test.

The pipeline, in order:

1. `pip install` every line of [robot_rest/requirements.txt](robot_rest/requirements.txt) into the current environment.
2. `django-admin startproject <project>` then `django-admin startapp core`.
3. Copy the bundled `.tpl` files into the new project, then run the local `sed()` closure over them to substitute placeholders and rename `.tpl` → `.py`.
4. `manage.py inspectdb` → written verbatim to `core/models.py`.
5. `drf_gen -m core/models.py -A` (from `django-drf-file-generator`) → produces `admin.py`, `urls.py`, `views.py`, `serializers.py`, which are moved into `core/` and the `drf_gen_build/` scratch dir is removed.
6. `pip freeze` → project `requirements.txt`.
7. `makemigrations`, `migrate`, `createsuperuser`, `collectstatic`.

### Two different requirements.txt files

- Root [requirements.txt](requirements.txt) / [dev-requirements.txt](dev-requirements.txt) — dependencies for developing *this* package.
- [robot_rest/requirements.txt](robot_rest/requirements.txt) — the payload installed at generation time into the *generated* project (django-jet, oauth-toolkit, swagger, social-oauth2, MySQL-python, …). Editing this changes what end users get installed.

### Template system

Templates live in [robot_rest/](robot_rest/) as `.tpl` and are copied out as `.py`. Placeholders are declared in `PLACEHOLDERS` and substituted by `substitute_line()`: `@projeto@`, `@HOST@`, `@USER@`, `@PASSWORD@`, `@NAME@`, `@SECRET@` (a 50-char key from `SystemRandom`).

Adding a new template requires **three** coordinated edits, or it will be missing at runtime for pip-installed users — the failure only shows up after `pip install`, never in a source checkout:
1. Create `robot_rest/<path>.tpl`.
2. Add the path to `TEMPLATE_PATHS` in [robot_rest/robot_rest.py](robot_rest/robot_rest.py).
3. Add it to `[tool.setuptools.package-data]` in [pyproject.toml](pyproject.toml).

[tests/test_packaging.py](tests/test_packaging.py) enforces all three, and the CI build job re-checks the wheel contents. If you add a template that is copied directly rather than rendered (like `urls.tpl`), add it to `STANDALONE_TEMPLATES` in that test.

### Generated settings layout

The generated project uses a split-settings package under `<project>/settings/`, not a single `settings.py`:

- `defaults.tpl` — everything shared (INSTALLED_APPS, JET admin, swagger, social auth backends, DRF config, pt-BR/America/Sao_Paulo locale).
- `dev.tpl` — `DEBUG=True`, MySQL creds baked in from the CLI flags, `AllowAny` permissions.
- `production.tpl` — `DEBUG=False`, creds read from environment variables, `IsAuthenticated`.
- `tests.tpl` — SQLite.
- `__init__.tpl` — selects the active module (`from .dev import *`; production is commented out).

The generator also writes a temporary top-level `settings.py` from `defaults.tpl` before `inspectdb` and deletes it at the end. This is **dead code**: once `settings/__init__.py` exists, Python resolves `<project>.settings` to the package, not the module. Safe to remove in Phase 1.

Generated URLs are versioned under `/v1/` — API routes from `core.urls`, plus swagger docs, OAuth2, social auth, token auth, and password reset. Admin uses django-jet.

## Modernization status

The tool itself now runs on Python 3.10+ (Phase 0). **The generated project has not been modernized yet** — it still targets the Django 1.8/1.10 era and pulls several dead dependencies. Do not treat the templates as current best practice:

- `drf_gen` (`django-drf-file-generator`) — the engine that generates `views.py`/`serializers.py`/`admin.py`/`urls.py` — last released **2016**. It is the project's single biggest risk; the plan is to bring codegen in-house.
- Also dead upstream: `django-rest-swagger` (2018), `django-jet` (2018), `django-rest-auth` (2019), `MySQL-python` (2014, Py2-only).
- Templates still use Django ≤1.x APIs removed in modern Django: `url()`, `include(admin.site.urls)`, function-based `password_reset` views, `oauth2_provider.ext.rest_framework`, `social.apps.django_app`.
- [robot_rest/settings/defaults.tpl](robot_rest/settings/defaults.tpl) ships a hardcoded personal Gmail address, `ALLOWED_HOSTS = ['*']`, `CORS_ORIGIN_ALLOW_ALL = True`, and `AllowAny`. The DB password arrives as an argv flag and is written in plaintext into `dev.py`.

Generation-time behavior that is known-undesirable and slated for Phase 1: `install_requirements()` pip-installs 27 packages into the user's active environment, and `createsuperuser` blocks the pipeline on interactive input.

## Conventions

Comments and docstrings in the source are in Brazilian Portuguese; generated templates likewise. Match the surrounding language when editing a file.
