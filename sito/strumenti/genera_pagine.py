#!/usr/bin/env python3
"""
genera_pagine.py - crea le due versioni del sito, una per lingua:

  modelli/index.html, modelli/storia.html  ->  it/*.html  e  fr/*.html

Le due versioni hanno lo stesso codice (comune/) e cambiano solo la
lingua: si modifica il modello, poi si lancia questo script.

Uso:  python3 sito/strumenti/genera_pagine.py
"""
from __future__ import annotations

import os

QUI = os.path.dirname(os.path.abspath(__file__))
SITO = os.path.normpath(os.path.join(QUI, ".."))
LINGUE = ["it", "fr"]
PAGINE = ["index.html", "storia.html"]


def main() -> None:
    for lang in LINGUE:
        os.makedirs(os.path.join(SITO, lang), exist_ok=True)
        for pagina in PAGINE:
            with open(os.path.join(SITO, "modelli", pagina), encoding="utf-8") as f:
                testo = f.read()
            assert "{{LANG}}" in testo, pagina
            with open(os.path.join(SITO, lang, pagina), "w", encoding="utf-8") as f:
                f.write(testo.replace("{{LANG}}", lang))
            print(f"scritto {lang}/{pagina}")


if __name__ == "__main__":
    main()
