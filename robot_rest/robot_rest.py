# coding: utf-8
# Esse programa tem o objetvo de facilitar a criação de projetos Django + Djangorestframework
# Autor: Alexandre Proença - linuxloco@gmail.com - alexandre.proenca@hotmail.com.br
# Floripa Dom 00:52 13/09/2015
# !/usr/bin/python
from argparse import ArgumentParser
from pkg_resources import resource_filename
import string
from random import choice
import os
import shutil
import subprocess
import sys


def main():
    """
    Metodo principal que vai receber os valores passados por linha de comando e manipular a criação de um projeto
    Django 1.8 + Djangorestframework 3.2, instala uma lista de pacotes predefinidos
    O metodo vai conectar em uma base de dados e fazer o mapeamento das entidades, transformando-as em objetos do tipo
    django.db.models, após este mapeamento configura o arquivo settings.py e gera mais quatro arquivos,
    dentro do app core, admin.py, urls.py, views.py, serializers.py, arquivos ja no padrao para ser usado com
    djangorestframework.
    """
    ap = ArgumentParser()
    ap.add_argument('-vv', '--verbose',
                    default=False,
                    help='Increase verbosity.')

    ap.add_argument('-ip',
                    required=True,
                    action='store',
                    dest='database_host',
                    help='Host address of the database')

    ap.add_argument('-user',
                    action='store',
                    required=True,
                    dest='database_user',
                    help='Username that have access database')

    ap.add_argument('-database',
                    action='store',
                    required=True,
                    dest='database_name',
                    help='The name of the database')

    ap.add_argument('-password',
                    action='store',
                    required=True,
                    dest='database_password',
                    help='Password to access the database')

    ap.add_argument('-project',
                    action='store',
                    required=True,
                    dest='project_name',
                    help='The name of the project.')

    args = ap.parse_args()

    if args.database_host:

        #TODO carregar essa lista de um arquivo de configuração
        subprocess.call(["pip", "install", "django", "django-oauth-toolkit", "django-admin-bootstrapped",
                         "django-cors-headers", "django-filter", "django-rest-auth",
                         "django-rest-swagger", "djangorestframework", "Markdown", "simplejson", "MySQL-python",
                         "django-url-filter", "django-drf-file-generator"])

        subprocess.call(["django-admin", "startproject", args.project_name])
        os.chdir(args.project_name)
        subprocess.call(["django-admin", "startapp", "core"])
        subprocess.call(['cp', resource_filename('robot_rest', 'urls.tpl'), args.project_name + r'/urls.py'])

        with open(args.project_name + r'/settings.py', 'wt') as fout:
            with open(resource_filename('robot_rest', 'settings.tpl'), 'rt') as fin:
                for line in fin:
                    if '@projeto@' in line:
                        fout.write(line.replace('@projeto@', args.project_name))
                    elif '@HOST@' in line:
                        fout.write(line.replace('@HOST@', args.database_host))
                    elif '@USER@' in line:
                        fout.write(line.replace('@USER@', args.database_user))
                    elif '@PASSWORD@' in line:
                        fout.write(line.replace('@PASSWORD@', args.database_password))
                    elif '@NAME@' in line:
                        fout.write(line.replace('@NAME@', args.database_name))
                    elif '@SECRET@' in line:
                        fout.write(line.replace('@SECRET@', ''.join([choice(string.letters + string.digits) for _ in range(50)])))
                    else:
                        fout.write(line)

        #subprocess.call(['python', 'manage.py', 'makemigrations'])

        #subprocess.call(['python', 'manage.py', 'createsuperuser'])
        models = subprocess.check_output(['python', 'manage.py', 'inspectdb'])
        with open("core/models.py", "w") as f:
            [f.write(l) for l in models]
        subprocess.call(["drf_gen", "-m", "core/models.py", "-A"])
        subprocess.call(["mv", "drf_gen_build/admin.py", "core"])
        subprocess.call(["mv", "drf_gen_build/urls.py", "core"])
        subprocess.call(["mv", "drf_gen_build/views.py", "core"])
        subprocess.call(["mv", "drf_gen_build/serializers.py", "core"])
        shutil.rmtree('drf_gen_build')
        with open('requirements.txt', 'w') as f:
            requirements = subprocess.check_output(['pip', 'freeze'])
            [f.write(l) for l in requirements]

        subprocess.call(['python', 'manage.py', 'migrate'])
        sys.exit(0)


if __name__ == "__main__":
    main()
