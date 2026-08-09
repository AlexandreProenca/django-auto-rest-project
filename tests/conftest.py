"""Configuracao compartilhada do pytest."""


def pytest_addoption(parser):
    parser.addoption(
        "--update-golden",
        action="store_true",
        default=False,
        help="Regrava os arquivos de referencia em tests/golden/ com a saida atual.",
    )
