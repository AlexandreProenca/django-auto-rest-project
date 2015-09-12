# coding: utf-8
# Extrator de modelos, este programa le o arquivo um arquivo no padrão django models.py, extrai as classes e os
# campos dos modelos e e opçionalmente pode gera quatro arquivos: urls.py, admin.py, serializers.py e views.py
# Autor: Alexandre Proença - linuxloco@gmail.com - alexandre.proenca@hotmail.com.br
# Floripa Dom 18:11 10/05/2015
# !/usr/bin/python
from ConfigParser import RawConfigParser
from argparse import ArgumentParser
from pkg_resources import resource_stream, resource_filename


import os
import shutil
import subprocess
import sys


def main():
    """
    Method main, set output dir and call a specific function, as given in the options
    :param argv:
    :return: None
    """
    #config = RawConfigParser()
    #config.readfp(resource_stream('robot_rest','config.ini'))

    #outputdir = config.get('outputdir', 'dir')
    #os.mkdir(outputdir) if not os.path.exists(outputdir) else outputdir

    ap = ArgumentParser()
    ap.add_argument('-vv', '--verbose',
                    default=False,
                    help='Increase verbosity.')

    ap.add_argument('-ip',
                    required=True,
                    action='store',
                    dest='database_host',
                    help='Host address of the database')

    ap.add_argument('-u',
                    action='store',
                    required=True,
                    dest='database_user',
                    help='Username that have access database')

    ap.add_argument('-b',
                    action='store',
                    required=True,
                    dest='database_name',
                    help='The name of the database')

    ap.add_argument('-p',
                    action='store',
                    required=True,
                    dest='database_password',
                    help='Password to access the database')

    ap.add_argument('-n',
                    action='store',
                    required=True,
                    dest='project_name',
                    help='The name of the project.')

    args = ap.parse_args()

    if args.database_host:
        subprocess.call(["pip", "install", "django", "django-oauth-toolkit", "django-admin-bootstrapped",
                         "django-cors-headers", "python-memcached", "django-filter", "django-rest-auth",
                         "django-rest-swagger", "djangorestframework", "Markdown", "simplejson", "MySQL-python",
                         "yet-another-django-profiler", "django-jet", "django-url-filter", "django-drf-file-generator"])

        subprocess.call(["django-admin", "startproject", args.project_name])
        os.chdir(args.project_name)
        subprocess.call(["django-admin", "startapp", "core"])
        subprocess.call(['cp', resource_filename('robot_rest', 'settings.tpl'), args.project_name + r'/settings.py'])
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
                    else:
                        fout.write(line)

        subprocess.call(['python', 'manage.py', 'makemigrations'])
        subprocess.call(['python', 'manage.py', 'migrate'])
        subprocess.call(['python', 'manage.py', 'createsuperuser'])
        models = subprocess.check_output(['python', 'manage.py', 'inspectdb'])
        f = open('core/models.py', 'w')
        [f.write(l) for l in models]
        f.close()
        subprocess.call(["drf_gen", "-m", "core/models.py", "-A"])
        subprocess.call(["mv", "drf_gem_build/admin.py", "core"])
        subprocess.call(["mv", "drf_gem_build/urls.py", "core"])
        subprocess.call(["mv", "drf_gem_build/views.py", "core"])
        subprocess.call(["mv", "drf_gem_build/serializers.py", "core"])
        shutil.rmtree('drf_gem_build')
        f = open('requirements.txt', 'w')
        requirements = subprocess.check_output(['pip', 'freeze'])
        [f.write(l) for l in requirements]
        sys.exit(0)

if __name__ == "__main__":
    main()
