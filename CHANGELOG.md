# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - unreleased

First release that runs on Python 3 and generates a project that boots on a
supported Django version. Version 0.5.4 could not start on any Python 3
interpreter, and its generated project targeted the Django 1.8 era.

### Breaking

- **Python 3.10+ is required.** Python 2 is no longer supported.
- **`-password` is no longer required.** It falls back to
  `$ROBOT_REST_DB_PASSWORD` and then to an interactive prompt. A password on
  the command line is visible in shell history and the process list.
- **Nothing is installed into your environment.** The tool used to
  `pip install` 27 packages into the active environment and to run
  `createsuperuser` interactively. It now writes a project directory and
  stops; the generated project ships its own `requirements.txt`.
- **The generated project is completely different.** Split settings package
  reading from `.env`, drf-spectacular instead of django-rest-swagger, the
  Django admin instead of django-jet, DRF token auth instead of
  django-rest-auth. Regenerating over an old project is not an upgrade path.
- **Django's own tables are skipped by default.** Previously, running against
  a database that already hosted a Django app published `auth_user` and
  `django_session` as REST routes. Use `--all-tables` for the old behaviour.
- The console script now points at `robot_rest.cli:main`.
  `robot_rest.robot_rest` remains as a compatibility shim.

### Added

- PostgreSQL and SQLite support via `-engine` (`mysql` remains the default).
  Drivers are optional extras: `[mysql]`, `[postgres]`.
- `--managed` marks the generated models `managed = True`, handing Django
  ownership of the schema. Off by default, and it warns when used.
- `--all-tables` opts back into introspecting Django's own tables.
- `-o/--output-dir` chooses where the project is created.
- `-port` for a non-default database port.
- `--version`.
- OpenAPI 3 schema, Swagger UI and ReDoc in the generated project.
- The generated project gets `.env`, `.env.example` and a `.gitignore`.

### Changed

- Code generation is now in-house. `django-drf-file-generator` (`drf_gen`,
  last released 2016) is gone; generated viewsets and routers use current DRF
  idiom.
- Templates use Jinja2 instead of `@PLACEHOLDER@` substitution.
- Introspection runs before anything is written to disk, so a bad connection,
  password or missing driver leaves nothing behind.
- The project is assembled in a temporary directory and moved into place, so
  the destination only appears once generation fully succeeded.
- Packaging moved from `setup.py` to `pyproject.toml`.
- CI moved from Travis to GitHub Actions, with a Python 3.10–3.13 matrix.

### Fixed

- The tool could not run at all on Python 3: `string.letters`, and iterating
  `subprocess.check_output` bytes wrote integers into `models.py`.
- Template substitution replaced only the first placeholder on a line.
- Generating into the current directory failed, because the pre-created
  directory counted as a namespace package and `startproject` rejected the
  name.
- A missing database driver printed a full traceback instead of one
  actionable line; the cleanup path masked the original error.
- Generated viewsets now order by `pk`. Paginating an unordered queryset can
  repeat or skip rows between pages.

### Security

- Database credentials and `SECRET_KEY` are written to `.env` (mode 600,
  gitignored) rather than into a Python file.
- Removed a hardcoded personal email address that shipped in every generated
  project.
- Removed `ALLOWED_HOSTS = ['*']` and `CORS_ORIGIN_ALLOW_ALL = True`; both now
  come from the environment.
- Default DRF permission is `IsAuthenticated`.
- The production settings add TLS, HSTS and secure-cookie options;
  `manage.py check --deploy` passes.
- Dropped the dead PyPI deploy credential from CI in favour of trusted
  publishing.

## [0.5.4] - 2021-04-07

Last release of the Python 2 line. See the git history for earlier changes.
