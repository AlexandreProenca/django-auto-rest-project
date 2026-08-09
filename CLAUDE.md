# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`django-auto-rest-project` is a **code generator**, not a Django app. It ships a single console script (`robot_rest`) that points at an existing MySQL, PostgreSQL, or SQLite database and scaffolds a complete Django + Django REST Framework project from that schema.

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

Against real MySQL and PostgreSQL (integration tests skip without this):

```bash
docker compose up -d --wait && docker compose run --rm tests
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

Version bump — single source of truth is `__version__` in [robot_rest/__init__.py](robot_rest/__init__.py), with a copy in `[tool.bumpversion]` that a test keeps in sync:

```bash
bump-my-version bump patch
```

Note this **commits and tags**, and pushing that tag triggers the PyPI publish job. Treat it as a release action, not a routine edit.

CI is [.github/workflows/ci.yml](.github/workflows/ci.yml): lint, a pytest matrix on Python 3.10–3.13, a build job that asserts every `.j2` template survives into the wheel, and a tag-triggered PyPI publish via trusted publishing (no secrets — needs the publisher configured on pypi.org).

## Architecture

Five modules, each with one job:

| Module | Responsibility |
|---|---|
| [cli.py](robot_rest/cli.py) | argparse, password resolution, error → exit code, next-steps output |
| [config.py](robot_rest/config.py) | `ProjectConfig`/`DatabaseConfig`, name validation, secret key |
| [introspect.py](robot_rest/introspect.py) | `inspectdb` in-process, table filtering, `ast` model discovery |
| [render.py](robot_rest/render.py) | Jinja2 environment and rendering |
| [project.py](robot_rest/project.py) | the pipeline, staging, and template→output map |

[robot_rest/robot_rest.py](robot_rest/robot_rest.py) is a back-compat shim re-exporting `main`; the console script points at `cli:main`.

The pipeline in `generate()`:

1. `introspect_schema()` — configures Django in-process (`settings.configure()` with only `DATABASES`), lists the tables, drops Django's own, and calls `inspectdb` under a fresh connection alias with the remainder. **This runs first, before anything touches the disk**, because connection/password/driver errors are the common failure and should leave nothing behind.
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

- **Django's own tables are filtered out by default** (`DJANGO_SYSTEM_TABLES` in [introspect.py](robot_rest/introspect.py)). If the target database has ever been used by a Django project — including one this tool generated and the user then migrated — `inspectdb` sees `auth_user`, `django_session`, and friends. Unfiltered, that publishes the auth tables as REST routes, and under `--managed` it hard-fails with `models.E028` ("db_table is used by multiple models"). `--all-tables` opts back in; skipped tables are always reported, never dropped silently.
- Filtering happens by passing the wanted tables to `inspectdb` positionally — it has no `--exclude`. If the filter leaves **zero** tables, `inspectdb` must not be called at all: with no positional args it introspects everything, undoing the filter.
- **inspectdb models are `managed = False` by default.** They have no tables in a test database, so generated tests assert routing, auth, and schema — never queries. `migrate` only creates Django's own tables. `--managed` flips this and hands Django ownership of the schema; the CLI warns because `migrate` can then alter or drop real data.
- **Generated viewsets order by `pk`.** Paginating an unordered queryset makes DRF emit `UnorderedObjectListWarning` and can repeat or skip rows across pages.
- `tests/test_generate.py` holds regression tests against removed Django APIs (`django.conf.urls`, `include(admin.site.urls)`, `oauth2_provider.ext.*`, …) and against the old security defaults. If you touch the project templates, those are what will catch a regression.

## Modernization status

Phases 0–4 are complete; the project is at 1.0.0 (unreleased — no tag pushed).

Verified against **live databases**, not just fixtures: SQLite and PostgreSQL 16 both go schema → generated project → `pip install -r requirements.txt` → `migrate` → generated tests → live CRUD (including a foreign key) → OpenAPI schema. MySQL shares the identical code path but has not been exercised against a live server here.

Docs are guarded by tests rather than trust: [tests/test_packaging.py](tests/test_packaging.py) asserts the version matches across files, that `CHANGELOG.md` mentions the current version, and that every CLI option appears in the README. That last one exists because the README silently drifted from the CLI more than once during this work.

Known gaps, in rough priority order:

- `DJANGO_SYSTEM_TABLES` covers `django.contrib` and `authtoken`. Tables from a third-party Django app in the same database are still introspected.
- The generated `requirements.txt` pins loose ranges (`Django>=4.2,<6.0`). No lockfile.
- Generated serializers use `fields = "__all__"`. Fine for a scaffold, but a new database column is exposed automatically.
- The "boot the generated project and serve traffic" check is still manual. CI generates a project and asserts its files, but does not start it.

### Containers

[docker-compose.yml](docker-compose.yml) runs MySQL 8.4 and PostgreSQL 16 seeded from [docker/initdb/](docker/initdb/), plus a `tests` service that runs the suite *inside* a container on the database network.

That inner container is not a convenience — it is the only way most machines can exercise the MySQL path at all, because `mysqlclient` needs MySQL's C client library and fails to build without it. The `test` stage of the [Dockerfile](Dockerfile) builds it on Debian where that library exists.

Two details worth preserving:

- The fixture password contains `#`. That is deliberate: unquoted, `django-environ` would read the rest of the `.env` line as a comment, and the generated project would connect with a truncated password. `render.envquote` is what prevents it, and the integration tests assert the round trip.
- Tests that exercise connection failures use `127.0.0.1:1` (instant refusal), not an unroutable address. An earlier version used TEST-NET, and each test blocked until timeout — the container suite took 226s instead of 1.4s.

### Releasing

`.github/workflows/ci.yml` publishes to PyPI on a pushed tag via trusted publishing. That requires the publisher to be configured on pypi.org first — it has never run, so the first release will need that set up.