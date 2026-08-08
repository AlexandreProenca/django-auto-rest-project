# Esse programa tem o objetvo de facilitar a criação de projetos Django + Djangorestframework
# Autor: Alexandre Proença - linuxloco@gmail.com - alexandre.proenca@hotmail.com.br
# Floripa Dom 00:52 13/09/2015
"""Gerador de projetos Django + Django REST Framework a partir de um banco MySQL."""

import os
import shutil
import string
import subprocess
import sys
from argparse import ArgumentParser
from pathlib import Path
from random import SystemRandom

#: Diretorio do proprio pacote, onde ficam os templates empacotados.
PACKAGE_DIR = Path(__file__).resolve().parent

#: Tamanho da SECRET_KEY gerada para o projeto.
SECRET_KEY_LENGTH = 50

#: Templates ``.tpl`` copiados para o projeto gerado e convertidos em ``.py``.
#: Qualquer template novo precisa ser listado aqui *e* declarado no
#: ``package-data`` do pyproject.toml, senão some na instalação via pip.
TEMPLATE_PATHS = (
    "settings/defaults",
    "settings/dev",
    "settings/production",
    "settings/tests",
    "settings/__init__",
    "tests/__init__",
    "tests/settingstest",
    "tests/test_rest_api",
)

#: Placeholders reconhecidos pelo :func:`substitute_line`.
PLACEHOLDERS = (
    "@projeto@",
    "@HOST@",
    "@USER@",
    "@PASSWORD@",
    "@NAME@",
    "@SECRET@",
)


def generate_secret_key(length=SECRET_KEY_LENGTH):
    """
    Gera uma SECRET_KEY aleatoria usando o gerador criptografico do sistema.

    :param length: numero de caracteres da chave.
    :return: str
    """
    alphabet = string.ascii_letters + string.digits
    rand = SystemRandom()
    return "".join(rand.choice(alphabet) for _ in range(length))


def build_context(project_name, database_host, database_user, database_password, database_name):
    """
    Monta o dicionario de substituicao usado nos templates.

    :return: dict com as chaves de :data:`PLACEHOLDERS`.
    """
    return {
        "@projeto@": project_name,
        "@HOST@": database_host,
        "@USER@": database_user,
        "@PASSWORD@": database_password,
        "@NAME@": database_name,
        "@SECRET@": generate_secret_key(),
    }


def substitute_line(line, context):
    """
    Substitui os placeholders de uma linha de template.

    Diferente da versao antiga (uma cadeia if/elif), substitui *todos* os
    placeholders presentes na linha, e nao apenas o primeiro.

    :param line: linha original do template.
    :param context: dict retornado por :func:`build_context`.
    :return: str
    """
    for placeholder, value in context.items():
        if placeholder in line:
            line = line.replace(placeholder, value)
    return line


def render_template(template_path, output_path, context):
    """
    Le um template ``.tpl``, aplica as substituicoes e grava o ``.py`` final.

    :param template_path: caminho do arquivo ``.tpl`` de origem.
    :param output_path: caminho do ``.py`` de destino.
    :param context: dict retornado por :func:`build_context`.
    """
    template_path = Path(template_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with template_path.open("rt", encoding="utf-8") as fin, output_path.open("wt", encoding="utf-8") as fout:
        for line in fin:
            fout.write(substitute_line(line, context))


def template_resource(*parts):
    """
    Resolve o caminho de um recurso empacotado dentro de ``robot_rest``.

    Substitui o antigo ``pkg_resources.resource_filename`` (depreciado); o
    pacote e sempre instalado descompactado, entao o caminho em disco vale.

    :param parts: componentes do caminho relativo ao pacote.
    :return: Path
    """
    return PACKAGE_DIR.joinpath(*parts)


def render_project_templates(project_dir, context, template_paths=TEMPLATE_PATHS):
    """
    Renderiza todos os templates do projeto e remove os ``.tpl`` copiados.

    :param project_dir: diretorio do pacote do projeto (``<projeto>/<projeto>``).
    :param context: dict retornado por :func:`build_context`.
    :param template_paths: iteravel com os caminhos de :data:`TEMPLATE_PATHS`.
    """
    project_dir = Path(project_dir)
    for path in template_paths:
        # A lista antiga misturava 'settings/dev' e '/settings/dev'; normaliza
        # para que Path() nao interprete o valor como caminho absoluto.
        relative = path.lstrip("/")
        source = project_dir / (relative + ".tpl")
        destination = project_dir / (relative + ".py")
        render_template(source, destination, context)
        source.unlink()


def install_requirements():
    """
    Instala no ambiente ativo os pacotes exigidos pelo projeto gerado.
    """
    requirements = template_resource("requirements.txt")
    with requirements.open("rt", encoding="utf-8") as handle:
        for line in handle:
            package = line.strip()
            if not package or package.startswith("#"):
                continue
            subprocess.call([sys.executable, "-m", "pip", "install", package])


def run_manage(*arguments):
    """
    Executa ``manage.py`` com o mesmo interpretador que roda o robot.

    :param arguments: argumentos passados ao manage.py.
    """
    return subprocess.call([sys.executable, "manage.py", *arguments])


def build_parser():
    """
    Constroi o parser de linha de comando.

    :return: ArgumentParser
    """
    ap = ArgumentParser(prog="robot_rest")
    ap.add_argument("-vv", "--verbose", default=False, help="Increase verbosity.")
    ap.add_argument(
        "-ip", required=True, action="store", dest="database_host", help="Host address of the database"
    )
    ap.add_argument(
        "-user",
        required=True,
        action="store",
        dest="database_user",
        help="Username that have access database",
    )
    ap.add_argument(
        "-database", required=True, action="store", dest="database_name", help="The name of the database"
    )
    ap.add_argument(
        "-password",
        required=True,
        action="store",
        dest="database_password",
        help="Password to access the database",
    )
    ap.add_argument(
        "-project", required=True, action="store", dest="project_name", help="The name of the project."
    )
    return ap


def main():
    """
    Metodo principal que recebe os valores passados por linha de comando e conduz a criação de um
    projeto Django + Djangorestframework, instalando uma lista de pacotes predefinidos.

    O metodo conecta em uma base de dados e faz o mapeamento das entidades, transformando-as em
    objetos do tipo django.db.models. Após esse mapeamento configura o settings.py e gera mais
    quatro arquivos dentro do app core -- admin.py, urls.py, views.py e serializers.py -- ja no
    padrao usado pelo djangorestframework.
    """
    args = build_parser().parse_args()

    project_name = args.project_name
    context = build_context(
        project_name=project_name,
        database_host=args.database_host,
        database_user=args.database_user,
        database_password=args.database_password,
        database_name=args.database_name,
    )

    install_requirements()

    subprocess.call(["django-admin", "startproject", project_name])
    os.chdir(project_name)
    subprocess.call(["django-admin", "startapp", "core"])

    package_dir = Path(project_name)

    shutil.copy(template_resource("urls.tpl"), package_dir / "urls.py")
    shutil.copytree(template_resource("settings"), package_dir / "settings", dirs_exist_ok=True)
    shutil.copytree(template_resource("tests"), package_dir / "tests", dirs_exist_ok=True)

    render_project_templates(package_dir, context)

    # settings.py temporario para que o inspectdb consiga carregar a configuracao.
    (package_dir / "settings.py").unlink(missing_ok=True)
    shutil.copy(package_dir / "settings" / "defaults.py", package_dir / "settings.py")

    models = subprocess.check_output([sys.executable, "manage.py", "inspectdb"], text=True)
    Path("core/models.py").write_text(models, encoding="utf-8")

    subprocess.call(["drf_gen", "-m", "core/models.py", "-A"])
    generated = Path("drf_gen_build")
    for filename in ("admin.py", "urls.py", "views.py", "serializers.py"):
        shutil.move(str(generated / filename), str(Path("core") / filename))
    shutil.rmtree(generated)

    frozen = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
    Path("requirements.txt").write_text(frozen, encoding="utf-8")

    run_manage("makemigrations")
    run_manage("migrate")
    run_manage("createsuperuser")
    run_manage("collectstatic")

    (package_dir / "settings.py").unlink(missing_ok=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
