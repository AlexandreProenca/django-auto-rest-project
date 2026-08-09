# Django Auto REST Project

[![CI](https://github.com/AlexandreProenca/django-auto-rest-project/actions/workflows/ci.yml/badge.svg)](https://github.com/AlexandreProenca/django-auto-rest-project/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/django-auto-rest-project.svg)](https://pypi.org/project/django-auto-rest-project/)
[![Python versions](https://img.shields.io/pypi/pyversions/django-auto-rest-project.svg)](https://pypi.org/project/django-auto-rest-project/)
[![License](https://img.shields.io/pypi/l/django-auto-rest-project.svg)](LICENSE.rst)

Point it at a database you already have, get a working Django + Django REST
Framework project out the other end — REST routes for every table, an admin,
OpenAPI docs, and user accounts.

*Aponte para um banco de dados que você já tem e receba um projeto Django +
Django REST Framework funcionando — rotas REST para cada tabela, admin,
documentação OpenAPI e contas de usuário.*

```bash
pip install 'django-auto-rest-project[mysql]'
robot_rest -ip 127.0.0.1 -user appuser -database appdb -project myapi
```

It reads your schema with Django's `inspectdb`, then generates a serializer, a
viewset, a router entry and an admin registration for every table — plus a
split settings package, an OpenAPI schema, Swagger UI, and sign up / login /
password reset pages that work on first run.

## Try it in two minutes

No database of your own needed. The repo ships a demo MySQL already populated
with a small store schema:

```bash
docker compose --profile demo up -d --wait mysql-demo
robot_rest -ip 127.0.0.1 -port 13307 -user demo -database loja -project lojaapi
```

Password is `demopass`. You get `category`, `product`, `customer`,
`customer_address`, `customer_order`, `order_item`, `tag` and `product_tag`
— so `/v1/product/` returns 25 rows across 3 pages, and `/v1/customer-order/`
shows foreign keys resolved.

Tear it down with `docker compose --profile demo down -v`.

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

Open <http://127.0.0.1:8000/v1/docs/> for the API, or
<http://127.0.0.1:8000/accounts/register/> to create an account.

## What you get

```
myapi
├── core                          # generated from your schema
│   ├── admin.py                  # one ModelAdmin per table
│   ├── models.py                 # from inspectdb
│   ├── serializers.py            # one ModelSerializer per table
│   ├── urls.py                   # DefaultRouter
│   ├── views.py                  # one ModelViewSet per table
│   └── migrations/
├── myapi
│   ├── settings/
│   │   ├── defaults.py           # shared, reads .env
│   │   ├── dev.py
│   │   ├── production.py         # passes `manage.py check --deploy`
│   │   └── tests.py
│   ├── tests/
│   │   ├── test_rest_api.py      # routing, auth and schema
│   │   └── test_accounts.py      # sign up, activation, login, password reset
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── templates/                    # account pages, ready to restyle
│   ├── registration/
│   └── django_registration/
├── .env                          # DB credentials + SECRET_KEY, mode 600
├── .env.example
├── .gitignore                    # already excludes .env
├── manage.py
└── requirements.txt
```

### Routes

| Path | What |
|---|---|
| `v1/` | one REST route per table |
| `v1/token-auth/` | POST username + password, get an API token |
| `v1/schema/` | OpenAPI 3 schema |
| `v1/docs/` | Swagger UI |
| `v1/redoc/` | ReDoc |
| `admin/` | Django admin |
| `api-auth/` | session login for the DRF browsable API |
| `accounts/register/` | sign up, sends an activation email |
| `accounts/activate/` | confirm the account |
| `accounts/login/`, `accounts/logout/` | session login |
| `accounts/password_reset/` | forgotten password, by email |
| `accounts/password_change/` | change while logged in |

## Usage

```
usage: robot_rest [-h] [--version] [-vv] [-engine ENGINE] [-ip DATABASE_HOST]
                  [-user DATABASE_USER] -database DATABASE_NAME
                  -project PROJECT_NAME [-port DATABASE_PORT] [--all-tables]
                  [--no-auth] [--managed] [-password DATABASE_PASSWORD]
                  [-o OUTPUT_DIR]
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
| `--no-auth` | Skip the account pages. They are included by default. |
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

## Accounts

Sign up, email activation, login, logout, password change and password reset
all work on first run — built on
[django-registration](https://django-registration.readthedocs.io/) plus
Django's own auth views.

The templates are generated too. `django-registration` deliberately ships
none, and `django.contrib.auth` has no `registration/login.html`, so without
them every account page would raise `TemplateDoesNotExist` the first time a
real user opened it. They are plain HTML in `templates/`, meant to be
restyled.

The flow:

1. `POST /accounts/register/` creates the account **inactive** and emails a link.
2. The link opens `/accounts/activate/?activation_key=…`, which shows a confirm
   button. Activation happens on the POST, so an email scanner following the
   link cannot activate somebody's account.
3. After that, `/accounts/login/` works, and `/v1/token-auth/` issues an API
   token for programmatic clients.

In development the emails print to the `runserver` console, so you can follow
the activation and reset links without configuring SMTP. Set
`ACCOUNT_ACTIVATION_DAYS` and `REGISTRATION_OPEN` in `.env` to change the link
lifetime or close sign-ups.

These are browser pages, not JSON endpoints. API clients authenticate with a
token from `/v1/token-auth/`. Pass `--no-auth` to leave the whole thing out.

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
Skipped tables are always listed in the output, and any model left pointing at
one of them is dropped rather than emitted broken. `--all-tables` includes
them.

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

To run the integration suite against real MySQL and PostgreSQL:

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
django-cors-headers, django-filter, drf-spectacular, django-environ and
django-registration. Optional additions (django-allauth for social login,
django-oauth-toolkit, django-unfold) are listed as comments in its
`requirements.txt`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Changes are listed in
[CHANGELOG.md](CHANGELOG.md).

## Authors

`django-auto-rest-project` was written by Alexandre Proença. See
[AUTHORS.rst](AUTHORS.rst).

Licensed under the MIT License — see [LICENSE.rst](LICENSE.rst).
