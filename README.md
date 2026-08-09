# Django Auto REST Project

[![CI](https://github.com/AlexandreProenca/django-auto-rest-project/actions/workflows/ci.yml/badge.svg)](https://github.com/AlexandreProenca/django-auto-rest-project/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/django-auto-rest-project.svg)](https://pypi.org/project/django-auto-rest-project/)
[![Python versions](https://img.shields.io/pypi/pyversions/django-auto-rest-project.svg)](https://pypi.org/project/django-auto-rest-project/)
[![License](https://img.shields.io/pypi/l/django-auto-rest-project.svg)](LICENSE.rst)

Point it at a database you already have, get a working Django + Django REST
Framework API out the other end.

*Aponte para um banco de dados que você já tem e receba uma API Django + Django
REST Framework funcionando.*

```bash
pip install 'django-auto-rest-project[mysql]'
robot_rest -ip 127.0.0.1 -user appuser -database appdb -project myapi
```

It reads your schema with Django's `inspectdb`, then generates a serializer, a
viewset, a router entry and an admin registration for every table — plus a
split settings package, an OpenAPI schema, and Swagger UI.

## What you get

```
myapi
├── core                      # generated from your schema
│   ├── admin.py              # one ModelAdmin per table
│   ├── models.py             # from inspectdb
│   ├── serializers.py        # one ModelSerializer per table
│   ├── urls.py               # DefaultRouter
│   ├── views.py              # one ModelViewSet per table
│   └── migrations/
├── myapi
│   ├── settings/
│   │   ├── defaults.py       # shared, reads .env
│   │   ├── dev.py
│   │   ├── production.py     # passes `manage.py check --deploy`
│   │   └── tests.py
│   ├── tests/                # smoke tests for the generated API
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── .env                      # DB credentials + SECRET_KEY, mode 600
├── .env.example
├── .gitignore                # already excludes .env
├── manage.py
└── requirements.txt
```

Routes:

| Path | What |
|---|---|
| `v1/` | one REST route per table |
| `v1/token-auth/` | POST username + password, get an API token |
| `v1/schema/` | OpenAPI 3 schema |
| `v1/docs/` | Swagger UI |
| `v1/redoc/` | ReDoc |
| `admin/` | Django admin |
| `accounts/` | login, logout, password reset |
| `api-auth/` | session login for the DRF browsable API |

## Getting started

```bash
python -m venv .venv && source .venv/bin/activate
pip install 'django-auto-rest-project[mysql]'
robot_rest -ip 127.0.0.1 -user appuser -database appdb -project myapi
```

Then run what it generated:

```bash
cd myapi
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open <http://127.0.0.1:8000/v1/docs/>.

## Usage

```
usage: robot_rest [-h] [--version] [-vv] [-engine ENGINE] [-ip DATABASE_HOST]
                  [-user DATABASE_USER] -database DATABASE_NAME
                  -project PROJECT_NAME [-port DATABASE_PORT] [--all-tables]
                  [--managed] [-password DATABASE_PASSWORD] [-o OUTPUT_DIR]
```

| Option | Meaning |
|---|---|
| `-database` | Database name, or the file path for sqlite. **Required.** |
| `-project` | Name of the project to create. **Required.** |
| `-engine` | `mysql` (default), `postgres` or `sqlite` |
| `-ip` | Database host. Not needed for sqlite. |
| `-user` | Database user. Not needed for sqlite. |
| `-port` | Database port. Defaults per engine. |
| `-password` | Database password. Optional — see below. |
| `--managed` | Hand Django ownership of the schema. Off by default. |
| `--all-tables` | Also map Django's own tables. Skipped by default. |
| `-o`, `--output-dir` | Where to create the project. Defaults to the current directory. |
| `-vv` | Increase verbosity. |
| `--version` | Print the version and exit. |

### Examples

```bash
# MySQL, password asked interactively
robot_rest -ip 187.45.196.236 -user nwpartner3 -database partnerdb -project webscrapy

# PostgreSQL
robot_rest -engine postgres -ip 187.45.196.236 -user nwpartner3 \
    -database partnerdb -project webscrapy

# SQLite: just a file path, no host, user or password
robot_rest -engine sqlite -database ./app.sqlite3 -project webscrapy

# password from the environment, for scripts
ROBOT_REST_DB_PASSWORD=... robot_rest -ip 187.45.196.236 -user nwpartner3 \
    -database partnerdb -project webscrapy
```

## Things worth knowing

**Your password does not have to go on the command line.** Anything passed to
`-password` is visible in your shell history and in the process list, so the
flag is optional: `robot_rest` reads `$ROBOT_REST_DB_PASSWORD` and otherwise
prompts for it.

**Nothing is installed into your environment.** The command writes a project
directory and stops. It does not `pip install`, migrate, or create a
superuser — the generated project ships its own `requirements.txt`.

**Your database is not modified.** `inspectdb` produces models with
`managed = False`, so `migrate` never creates or alters your existing tables.
`--managed` opts into the opposite, and warns you when it does.

**Django's own tables are skipped.** If the target database already hosts a
Django app — including one this tool generated and you then migrated —
`auth_user` and `django_session` would otherwise be published as REST routes.
Skipped tables are always listed in the output. `--all-tables` includes them.

**Secrets stay out of your source tree.** Connection details and the generated
`SECRET_KEY` go to `.env` (mode 600, already in the generated `.gitignore`),
never into a Python file. `.env.example` documents every variable.

## Docker

Run the tool without installing anything:

```bash
docker build -t robot-rest .
docker run --rm -v "$PWD/out:/work" --user "$(id -u):$(id -g)" robot-rest \
    -engine postgres -ip host.docker.internal -user appuser \
    -database shopdb -project myapi
```

The generated project lands in `./out`, owned by you rather than root.

### Try it without a database of your own

`docker compose` ships a demo MySQL already populated with a small store
schema — 8 tables, foreign keys, an N:N join, and enough rows to see the API
paginate:

```bash
docker compose --profile demo up -d --wait mysql-demo
robot_rest -ip 127.0.0.1 -port 13307 -user demo -database loja -project lojaapi
```

That gives you `category`, `product`, `customer`, `customer_address`,
`customer_order`, `order_item`, `tag` and `product_tag` — so
`/v1/product/` returns 25 rows across 3 pages, and `/v1/customer-order/`
shows foreign keys resolved.

Password is `demopass`. Tear it down with `docker compose --profile demo down -v`.

### Running the integration suite

```bash
docker compose up -d --wait
docker compose run --rm tests
docker compose down -v
```

## Requirements

- Python 3.10+
- A MySQL, PostgreSQL or SQLite database to read

Install the driver for your database with the tool:

```bash
pip install 'django-auto-rest-project[mysql]'      # mysqlclient
pip install 'django-auto-rest-project[postgres]'   # psycopg
```

SQLite needs no extra driver.

The generated project depends on Django, Django REST Framework,
django-cors-headers, django-filter, drf-spectacular and django-environ.
Optional extras (dj-rest-auth, django-oauth-toolkit, django-unfold) are listed
as comments in its `requirements.txt`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Changes are listed in
[CHANGELOG.md](CHANGELOG.md).

## Authors

`django-auto-rest-project` was written by Alexandre Proença. See
[AUTHORS.rst](AUTHORS.rst).

Licensed under the MIT License — see [LICENSE.rst](LICENSE.rst).
