"""
Shim de compatibilidade.

A logica virou os modulos :mod:`robot_rest.cli`, :mod:`robot_rest.config`,
:mod:`robot_rest.introspect`, :mod:`robot_rest.project` e
:mod:`robot_rest.render`. Este modulo existe apenas para nao quebrar quem
chamava ``python -m robot_rest.robot_rest`` ou importava ``main`` daqui.
"""

from __future__ import annotations

import sys

from .cli import build_parser, main

__all__ = ["build_parser", "main"]


if __name__ == "__main__":
    sys.exit(main())
