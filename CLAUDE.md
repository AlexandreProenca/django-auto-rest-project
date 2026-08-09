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

Split-settings package under `<project>/settings/`, all values from the environment via `django-environ`:

- `defaults.py.j2` — shared config; reads `.env`. `IsAuthenticated` by default, `CORS_ALLOWED_ORIGINS` (never allow-all), drf-spectacular as the schema class.
- `dev.py.j2` — `DEBUG=True`, console email. Deliberately does **not** set `ALLOWED_HOSTS`; that stays a single source of truth in `.env`.
- `production.py.j2` — `DEBUG=False` plus TLS/HSTS/secure-cookie hardening. `manage.py check --deploy` passes clean.
- `tests.py.j2` — in-memory SQLite. Needed because inspectdb models are `managed = False` and have no tables in a test database.

Three untracked-by-default files are also generated: `.env` (chmod 600, holds the DB password and `SECRET_KEY`), `.env.example`, and `.gitignore` that excludes `.env`.

Generated URLs: `admin/`, `accounts/` (Django's built-in auth views), `api-auth/`, `v1/` (routes from `core.urls`), `v1/token-auth/`, `v1/schema/`, `v1/docs/`, `v1/redoc/`.

### Constraints worth knowing

- **inspectdb models are `managed = False`.** They have no tables in a test database, so generated tests assert routing, auth, and schema — never queries. `migrate` only creates Django's own tables.
- **Generated viewsets order by `pk`.** Paginating an unordered queryset makes DRF emit `UnorderedObjectListWarning` and can repeat or skip rows across pages.
- `tests/test_generate.py` holds regression tests against removed Django APIs (`django.conf.urls`, `include(admin.site.urls)`, `oauth2_provider.ext.*`, …) and against the old security defaults. If you touch the project templates, those are what will catch a regression.

## Modernization status

Phases 0–2 are done: the tool runs on Python 3.10+, owns its codegen, and **the generated project boots on Django 5.2 and serves a working API** — verified by installing its requirements in a clean venv, running `migrate`, its own test suite, `check --deploy`, and live CRUD plus the OpenAPI schema.

Remaining (Phase 3+):

- MySQL is the only engine the CLI exposes. `DatabaseConfig`/`run_inspectdb` already take any engine — SQLite and PostgreSQL work internally and are used by the tests — so this is mostly a CLI flag plus documentation.
- No `--managed/--unmanaged` flag: inspectdb marks models unmanaged, so Django will not create or migrate those tables.
- The README still has stale badges (Codacy, readthedocs, StackShare, Gitter) and a `docs/` site that does not exist.
