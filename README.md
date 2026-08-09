###Django Auto REST Project

[![Badge](https://github.com/AlexandreProenca/django-auto-rest-project/actions/workflows/ci.yml/badge.svg)](https://github.com/AlexandreProenca/django-auto-rest-project/actions/workflows/ci.yml "CI")
[![Badge](https://img.shields.io/pypi/v/django-auto-rest-project.svg)](https://pypi.python.org/pypi/django-auto-rest-project "Pypi")
[![Badge](https://img.shields.io/pypi/dd/django-auto-rest-project.svg)](https://pypi.python.org/pypi/django-auto-rest-project "Pypi")
[![Badge](https://img.shields.io/pypi/pyversions/django-auto-rest-project.svg)](https://pypi.python.org/pypi/django-auto-rest-project "Pypi")
[![Badge](https://img.shields.io/pypi/l/django-auto-rest-project.svg)](https://pypi.python.org/pypi/django-auto-rest-project "Pypi")
[![Badge](https://img.shields.io/pypi/wheel/django-auto-rest-project.svg)](https://pypi.python.org/pypi/django-auto-rest-project "Pypi")
[![Badge](https://img.shields.io/pypi/format/django-auto-rest-project.svg)](https://pypi.python.org/pypi/django-auto-rest-project "Pypi")
[![Badge](https://img.shields.io/pypi/implementation/django-auto-rest-project.svg)](https://pypi.python.org/pypi/django-auto-rest-project "Pypi")
[![Badge](https://img.shields.io/pypi/status/django-auto-rest-project.svg)](https://pypi.python.org/pypi/django-auto-rest-project "Pypi")
[![Badge](https://api.codacy.com/project/badge/50515222d332430aba11bcbe76706f14)](https://www.codacy.com/app/linuxloco/django-auto-rest-project "Codacy")
[![Badge](https://readthedocs.org/projects/django-auto-rest-project/badge/?version=latest)](http://django-auto-rest-project.readthedocs.org/en/latest/ "ReadDocs")
[![Badge](http://img.shields.io/badge/tech-stack-0690fa.svg?style=flat)](http://stackshare.io/AlexandreProenca/django-auto-rest-project "StackShare")
[![Badge](https://img.shields.io/badge/GITTER-join%20chat-green.svg)](https://gitter.im/AlexandreProenca/devfriends?utm_source=share-link&utm_medium=link&utm_campaign=share-link "Livechat")

-----------

[![Badge](https://img.shields.io/badge/english-ok-blue.svg)](https://img.shields.io/badge/english-ok-green.svg" Livechat")

This package aims to facilitate the creation of Django projects with Django Rest Framework, just type database connetions informations and the robot will gives you a Django RESTful project based on your mysql database.
Ridiculously simple and fast to use, just install the package and type the command like the exemple below.
    
[![Badge](https://img.shields.io/badge/portugues--brasil-ok-green.svg)](https://img.shields.io/badge/portugues--brasil-ok-green.svg" Livechat")

Este pacote tem o objectivo de facilitar a criação de projetos Django + Django Rest Framework, basta apenas digitar os dados de conexão com seu banco de dados e o robo vai criar um projeto Django RESTful baseado no seu banco de dados mysql.
Ridiculamente fácil de usar, basta instalar o pacote e digitar o comando, como no exemplo abaixo:

`$pip install django-auto-rest-project`

`$robot_rest -ip 227.33.126.233 -user punkhard -database banddb -project alsage -password jhhf4`

Some packages included

Modern template for Django admin interface with improved functionality

[![Badge](https://raw.githubusercontent.com/geex-arts/jet/static/screen1.png)](http://readdocs.com" Jet Admin")

Swagger the best way to document your API

[![Badge](http://artsy.github.io/images/2013-06-21-adding-api-documentation-with-grape-swagger/swagger-ui.png)](http://readdocs.com" Swagger")


###Safe Installation

    Easiest and safe way to install this library is by using pip and virtualenv:
    
    $ virtualenv myenv
    $ cd myenv
    $ source bin/activate
    $ mkdir myproject
    $ cd myproject
    $ pip install django-auto-rest-project

Usage
-----
    usage: robot_rest [-h] [--version] [-vv] [-engine ENGINE] [-ip DATABASE_HOST]
                      [-user DATABASE_USER] -database DATABASE_NAME
                      -project PROJECT_NAME [-port DATABASE_PORT] [--all-tables]
                      [--managed] [-password DATABASE_PASSWORD] [-o OUTPUT_DIR]

    optional arguments:
    -h, --help                  Show this help message and exit

    --version                   Show the version and exit

    -vv, --verbose              Increase verbosity.

    -engine ENGINE              mysql (default), postgres or sqlite

    -ip DATABASE_HOST           Host address of the database. Not needed for sqlite.

    -user DATABASE_USER         Username that have access database. Not needed for sqlite.

    -database DATABASE_NAME     The name of the database

    -project PROJECT_NAME       The name of the project.

    -port DATABASE_PORT         Database port (default: per engine)

    --all-tables                Also map Django's own tables (auth_user, django_session...).
                                They are skipped by default.

    --managed                   Mark models as managed = True, handing Django ownership
                                of the schema. Off by default: migrate never touches
                                your existing tables.

    -password DATABASE_PASSWORD Password to access the database. Optional -- see below.

    -o, --output-dir OUTPUT_DIR Where to create the project (default: current directory)

Exemples:

    # password asked interactively (recommended)
    robot_rest -ip 187.45.196.236 -user nwpartner3 -database partnerdb -project webscrapy

    # PostgreSQL
    robot_rest -engine postgres -ip 187.45.196.236 -user nwpartner3 \
        -database partnerdb -project webscrapy

    # SQLite: just the file path, no host, user or password
    robot_rest -engine sqlite -database ./app.sqlite3 -project webscrapy

    # password from the environment, for scripts
    ROBOT_REST_DB_PASSWORD=... robot_rest -ip 187.45.196.236 -user nwpartner3 \
        -database partnerdb -project webscrapy

A password passed with `-password` is visible in your shell history and in the
process list, so it is no longer required: `robot_rest` reads
`$ROBOT_REST_DB_PASSWORD` and otherwise prompts for it.

The command only writes the project directory. It does not install packages
into your environment, run migrations, or create a superuser -- the generated
project ships its own `requirements.txt` and the next steps are printed when
generation finishes.

###Project's Scheme

    |project_name
    ├── core
    │   ├── admin.py
    │   ├── __init__.py
    │   ├── migrations
    │   │   └── __init__.py
    │   ├── models.py
    │   ├── serializers.py
    │   ├── tests.py
    │   ├── urls.py
    │   └── views.py
    ├── manage.py
    └── project_name
        ├── __init__.py
        ├── settings.py
        ├── urls.py
        └── wsgi.py


###Packages installed in the generated project

    Django
    djangorestframework
    django-cors-headers
    django-filter
    drf-spectacular
    django-environ
    mysqlclient            (or psycopg, depending on the database)

Six packages instead of the 27 older versions pulled in. Optional additions
are listed as comments in the generated `requirements.txt` (dj-rest-auth,
django-oauth-toolkit, django-unfold).

Nothing is installed into your environment by `robot_rest` itself -- the
generated project ships this list and you install it where you want.

###Urls that will be created

    admin/                  Django admin
    accounts/               login, logout and password reset (Django built-ins)
    api-auth/               session login for the DRF browsable API
    v1/                     one REST route per table, from core/urls.py
    v1/token-auth/          POST username+password, get an API token
    v1/schema/              OpenAPI 3 schema
    v1/docs/                Swagger UI
    v1/redoc/               ReDoc

###Configuration

Connection details and the generated `SECRET_KEY` are written to `.env`
(mode 600, already listed in the generated `.gitignore`) -- never into a
Python file. `.env.example` documents every supported variable.

`settings/` is split into `defaults`, `dev`, `production` and `tests`.
`python manage.py check --deploy` passes with the production settings.

###Requirements
    Python 3.10+ (to run the robot_rest command)
    A MySQL, PostgreSQL or SQLite database to introspect

Install the driver for your database along with the tool:

    pip install 'django-auto-rest-project[mysql]'
    pip install 'django-auto-rest-project[postgres]'

SQLite needs no extra driver.

###Notes

Tables belonging to Django itself (`auth_user`, `django_session`, ...) are
skipped, so pointing the tool at a database that already hosts a Django app
will not publish its auth tables as REST routes. Pass `--all-tables` to
include them anyway; skipped tables are always listed in the output.

Models come out of `inspectdb` as `managed = False`, so `migrate` never
creates or alters your existing tables. Pass `--managed` to hand Django
ownership of the schema instead.

##Authors
`django-auto-rest-project` was written by `Alexandre Proença <alexandre.proenca@hotmail.com.br>`_.
