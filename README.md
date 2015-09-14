###Django Auto REST Project

[![Badge](https://travis-ci.org/AlexandreProenca/django-auto-rest-project.svg?branch=master)](https://travis-ci.org/AlexandreProenca/django-auto-rest-project "Travis CI")
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
    usage: robot_rest [-h] [-vv VERBOSE] -ip DATABASE_HOST -user DATABASE_USER -database DATABASE_NAME -password DATABASE_PASSWORD -project PROJECT_NAME

    optional arguments:
    -h, --help                  Show this help message and exit
    
    -vv VERBOSE, --verbose      VERBOSE Increase verbosity.
    
    -ip DATABASE_HOST           Host address of the database
    
    -user DATABASE_USER         Username that have access database
    
    -database DATABASE_NAME     The name of the database
    
    -password DATABASE_PASSWORD Password to access the database
    
    -project PROJECT_NAME       The name of the project.
    

Exemples:

    robot_rest -ip 187.45.196.236 -user nwpartner3 -database partnerdb -project webscrapy -password sdf435*7

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


###Packages that will be installed

    cached-property (1.2.0)
    Django (1.8.4)
    django-admin-bootstrapped (2.5.5)
    django-auto-rest-project (0.1.1)
    django-braces (1.8.1)
    django-cors-headers (1.1.0)
    django-drf-file-generator (0.1.0)
    django-filter (0.11.0)
    django-jet (0.0.9)
    django-oauth-toolkit (0.9.0)
    django-rest-auth (0.5.0)
    django-rest-swagger (0.3.4)
    django-url-filter (0.2.0)
    djangorestframework (3.2.3)
    enum34 (1.0.4)
    funcsigs (0.4)
    Markdown (2.6.2)
    mock (1.3.0)
    MySQL-python (1.2.5)
    oauthlib (1.0.1)
    pbr (1.7.0)
    python-memcached (1.57)
    PyYAML (3.11)
    setuptools (3.6)
    simplejson (3.8.0)
    six (1.9.0)
    wsgiref (0.1.2)
    yet-another-django-profiler (1.0.0)

###Urls that will be created
    url(r'^admin/', include(admin.site.urls)),
    url(r'^docs/', include('rest_framework_swagger.urls')),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^', include('core.urls')),
    
###Requirements
    Python 2.7, 3.x, pypy or pypy3
    Django 1.8+ (there are plans to support older Django versions)
    Django REST Framework 2 or 3

##Authors
`django-auto-rest-project` was written by `Alexandre Proença <alexandre.proenca@hotmail.com.br>`_.
