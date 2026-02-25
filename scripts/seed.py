"""
Wrapper de seed para executar a partir do diretório raiz do projeto.

Uso:
    python scripts/seed.py
"""
import sys
import os

# Adicionar o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

from seed import seed  # noqa: E402

if __name__ == "__main__":
    seed()
