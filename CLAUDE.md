# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`django-auto-rest-project` is a **code generator**, not a Django app. It ships a single console script (`robot_rest`) that points at an existing MySQL database and scaffolds a complete Django + Django REST Framework project from that schema.

The distribution name on PyPI is `django-auto-rest-project`; the Python package is `robot_rest`.

```bash
robot_rest -ip 127.0.0.1 -user someuser -database somedb -project myproject -password secret
```

`-password` is optional — it falls back to `$ROBOT_REST_DB_PASSWORD`, then an interactive prompt, because argv leaks into shell history and the process table. The command creates `./<project_name>/` (or `-o <dir>`) and nothing else: it does not install packages, migrate, or prompt for a superuser.

## Commands

Packaging is `pyproject.toml` + setuptools. The package depends on Django and Jinja2; DB drivers are extras (`[mysql]`, `[postgres]`). Tests need no database — they drive `inspectdb` against SQLite fixtures.

```bash
pip install -e ".[dev]"
```

```bash
python -m pytest
```

Single test:

```bash
python -m pytest tests/test_codegen.py::TestUrls::test_registers_every_model_on_the_router
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

CI is [.github/workflows/ci.yml](.github/workflows/ci.yml): lint, a pytest matrix on Python 3.10–3.13, a build job that asserts every `.j2` template survives into the wheel, and a tag-triggered PyPI publish via trusted publishing (no secrets — needs the publisher configured on pypi.org).

## Architecture

Five modules, each with one job:

| Module | Responsibility |
|---|---|
| [cli.py](robot_rest/cli.py) | argparse, password resolution, error → exit code, next-steps output |
| [config.py](robot_rest/config.py) | `ProjectConfig`/`DatabaseConfig`, name validation, secret key |
| [introspect.py](robot_rest/introspect.py) | `inspectdb` in-process + `ast` model discovery |
| [render.py](robot_rest/render.py) | Jinja2 environment and rendering |
| [project.py](robot_rest/project.py) | the pipeline, staging, and template→output map |

[robot_rest/robot_rest.py](robot_rest/robot_rest.py) is a back-compat shim re-exporting `main`; the console script points at `cli:main`.

The pipeline in `generate()`:

1. `run_inspectdb()` — configures Django in-process (`settings.configure()` with only `DATABASES`) and calls `inspectdb` under a fresh connection alias. **This runs first, before anything touches the disk**, because connection/password/driver errors are the common failure and should leave nothing behind.
2. `discover_models()` — `ast`-parses the returned source for classes subclassing `models.Model`. No import, so it survives `inspectdb` output that wouldn't load.
3. `scaffold()` — `startproject` + `startapp core` in-process, into a **temp staging directory**, then deletes the `settings.py` that `startproject` wrote (the rendered `settings/` package replaces it).
4. `render_project()` — renders every template in `PROJECT_TEMPLATES` and `CORE_TEMPLATES`.
5. `shutil.move()` staging → destination.

### Why staging matters

Two non-obvious reasons the project is built in a temp dir and moved:

- An empty directory at the destination counts as a **namespace package**, so `startproject` rejects the name with "conflicts with an existing module" — and this fires in the most common case, generating into the current directory. Pre-creating the target directory is what broke it.
- The destination only appears once generation fully succeeded; any failure vanishes with the temp dir. There is no partial-project cleanup path to maintain.

### Codegen replaces drf_gen

`django-drf-file-generator` (last release 2016) is gone. `core/serializers.py`, `views.py`, `urls.py`, and `admin.py` are rendered from templates in [robot_rest/templates/core/](robot_rest/templates/core/) using modern DRF idiom (`ModelViewSet` + `DefaultRouter`). These four files carry a "regenerated on every run" header — customizations belong elsewhere.

Route naming: `AlbumTrack` → URL `album-track`, basename `album_track`, via `camel_to_snake()`.

### Environment

The tool depends on Django and Jinja2 and uses **its own** Django to introspect. It no longer pip-installs anything into the user's environment, and no longer runs `createsuperuser`/`migrate`/`collectstatic` — the generated project ships a `requirements.txt` and the CLI prints next steps. DB drivers are extras: `[mysql]`, `[postgres]`.

### Template system

Templates are Jinja2 `.j2` files under [robot_rest/templates/](robot_rest/templates/). Context: `project_name`, `secret_key`, `database` (a Django `DATABASES['default']` dict, so `{{ database.NAME }}`), and `models`.

The environment uses **`StrictUndefined`** — a typo in a template raises instead of silently rendering an empty file. Keep it that way.

Adding a template requires two coordinated edits, or it goes missing only after `pip install`, never in a source checkout:
1. Create the `.j2` under `robot_rest/templates/`.
2. Register it in `PROJECT_TEMPLATES` or `CORE_TEMPLATES` in [robot_rest/project.py](robot_rest/project.py).

`package-data` in [pyproject.toml](pyproject.toml) uses a recursive glob, so it usually needs no change. [tests/test_packaging.py](tests/test_packaging.py) enforces the mapping in both directions (no orphan templates, no dangling references), and the CI build job re-checks the wheel.

### Generated settings layout

The generated project uses a split-settings package under `<project>/settings/`, not a single `settings.py`:

- `defaults.py.j2` — everything shared (INSTALLED_APPS, JET admin, swagger, social auth backends, DRF config, pt-BR/America/Sao_Paulo locale).
- `dev.py.j2` — `DEBUG=True`, connection details baked in from the CLI flags, `AllowAny` permissions.
- `production.py.j2` — `DEBUG=False`, creds read from environment variables, `IsAuthenticated`.
- `tests.py.j2` — SQLite.
- `__init__.py.j2` — selects the active module (`from .dev import *`; production is commented out).

Generated URLs are versioned under `/v1/` — API routes from `core.urls`, plus swagger docs, OAuth2, social auth, token auth, and password reset. Admin uses django-jet.

## Modernization status

The tool runs on Python 3.10+ and no longer depends on `drf_gen` (Phase 0 + Phase 1). **The generated project's `settings/` and project-level `urls.py` have not been modernized yet** — they still target the Django 1.8/1.10 era. `core/` is current; the project-level templates are not. Do not treat them as best practice:

- Project templates still use Django APIs removed in modern Django: `url()`, `include(admin.site.urls)`, function-based `password_reset` views, `oauth2_provider.ext.rest_framework`, `social.apps.django_app`. **A generated project will not boot until these are fixed.**
- The emitted `requirements.txt` still lists packages that are dead upstream: `django-rest-swagger` (2018), `django-jet` (2018), `django-rest-auth` (2019). Replacements: drf-spectacular, django-jet-reboot/unfold, dj-rest-auth.
- [robot_rest/templates/project/settings/defaults.py.j2](robot_rest/templates/project/settings/defaults.py.j2) ships a hardcoded personal Gmail address, `ALLOWED_HOSTS = ['*']`, `CORS_ORIGIN_ALLOW_ALL = True`, and `AllowAny`. The DB password is still written in plaintext into `dev.py`.

Fixing all of the above is Phase 2.
