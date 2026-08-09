"""
Comparacao byte a byte da saida do codegen com arquivos de referencia.

As asserts por substring dos outros testes nao pegam mudanca de formatacao,
import perdido ou linha em branco a mais -- coisas que num gerador de codigo
aparecem direto no arquivo que o usuario abre. Para atualizar a referencia
depois de uma mudanca intencional, rode:

    python -m pytest tests/test_golden.py --update-golden
"""

from pathlib import Path

import pytest

from robot_rest.introspect import DiscoveredModel
from robot_rest.render import render

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"

MODELS = [DiscoveredModel(name="AlbumTrack"), DiscoveredModel(name="Artist")]

CONTEXT = {
    "project_name": "goldenapi",
    "secret_key": "x" * 50,
    "database": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "goldendb",
        "USER": "u",
        "PASSWORD": "p",
        "HOST": "h",
        "PORT": "3306",
    },
    "models": MODELS,
}

#: (template, arquivo de referencia, modelos)
CASES = [
    ("core/serializers.py.j2", "serializers.py", MODELS),
    ("core/views.py.j2", "views.py", MODELS),
    ("core/urls.py.j2", "urls.py", MODELS),
    ("core/admin.py.j2", "admin.py", MODELS),
    ("core/serializers.py.j2", "empty_serializers.py", []),
    ("core/urls.py.j2", "empty_urls.py", []),
]


@pytest.mark.parametrize(("template", "golden", "models"), CASES, ids=[c[1] for c in CASES])
def test_generated_output_matches_golden(template, golden, models, request):
    rendered = render(template, {**CONTEXT, "models": models})
    path = GOLDEN_DIR / golden

    if request.config.getoption("--update-golden"):
        path.write_text(rendered, encoding="utf-8")
        pytest.skip(f"referencia atualizada: {golden}")

    expected = path.read_text(encoding="utf-8")
    assert rendered == expected, (
        f"{golden} mudou. Se foi de proposito, rode "
        f"'python -m pytest tests/test_golden.py --update-golden' e revise o diff."
    )


def test_every_golden_file_is_covered():
    referenced = {golden for _, golden, _ in CASES}
    on_disk = {p.name for p in GOLDEN_DIR.glob("*.py")}
    assert on_disk == referenced
