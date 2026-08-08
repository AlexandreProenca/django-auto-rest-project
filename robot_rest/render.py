"""Renderizacao dos templates Jinja2 empacotados."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

#: Diretorio do proprio pacote.
PACKAGE_DIR = Path(__file__).resolve().parent

#: Raiz dos templates ``.j2``.
TEMPLATES_DIR = PACKAGE_DIR / "templates"

#: Sufixo dos templates; o arquivo gerado e o nome sem o sufixo.
TEMPLATE_SUFFIX = ".j2"


def build_environment(templates_dir: Path | None = None) -> Environment:
    """
    Monta o ambiente Jinja2 usado para gerar codigo Python.

    ``StrictUndefined`` e proposital: uma variavel faltando quebra a geracao
    em vez de gravar um arquivo silenciosamente incompleto. ``autoescape``
    fica desligado porque a saida e codigo Python, nao HTML.
    """
    return Environment(
        loader=FileSystemLoader(str(templates_dir or TEMPLATES_DIR)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
    )


def render(template_name: str, context: dict, environment: Environment | None = None) -> str:
    """
    Renderiza um template e devolve o conteudo como string.

    :param template_name: caminho do template relativo a :data:`TEMPLATES_DIR`.
    :param context: variaveis disponiveis no template.
    """
    env = environment or build_environment()
    return env.get_template(template_name).render(**context)


def render_to(
    template_name: str,
    output_path: Path,
    context: dict,
    environment: Environment | None = None,
) -> Path:
    """
    Renderiza um template direto para um arquivo, criando os diretorios pai.

    :return: o caminho gravado.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render(template_name, context, environment), encoding="utf-8")
    return output_path


def iter_template_names(templates_dir: Path | None = None) -> list[str]:
    """
    Lista todos os templates empacotados, com caminho relativo e barras ``/``.

    Usado pelos testes de empacotamento para garantir que nenhum template
    fique de fora da distribuicao.
    """
    root = templates_dir or TEMPLATES_DIR
    return sorted(str(p.relative_to(root).as_posix()) for p in root.rglob(f"*{TEMPLATE_SUFFIX}"))
