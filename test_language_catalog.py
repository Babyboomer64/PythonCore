# test_language_catalog.py
# -*- coding: utf-8 -*-
"""
Demonstration app for the domain-aware LanguageCatalog via language_service.
Loads a single domain-aware messages.json and showcases:
- getting texts in different contexts (domains),
- hierarchical fallback (GLOBAL.DATABASE.ORACLE -> GLOBAL.DATABASE -> GLOBAL),
- formatting with variables,
- listing labels and languages per domain.

Run:
    python test_language_catalog.py
"""
from __future__ import annotations

from language_service import (
    init_language,
    set_language_context,
    text,
    fmt,
    add_domain_file,   # not used, but here to show public API
    add_language_file, # (legacy) not used
    add_single_language_file # not used
)
from language_catalog import ROOT_DOMAIN

MESSAGES_PATH = "messages.json"

def show(label: str, lang: str | None = None) -> None:
    try:
        print(f"{label} ({'default-lang' if lang is None else lang}): {text(label, lang=lang)}")
    except Exception as e:
        print(f"{label} -> [missing] {e}")

def main() -> None:
    # 1) initialize language with domain-aware messages.json
    init_language(
        MESSAGES_PATH,
        default_lang="DE",
        allowed_langs={"DE","EN"},
        context=ROOT_DOMAIN,
        domain_aware=True
    )

    print("=== Context:", ROOT_DOMAIN, "===")
    set_language_context(ROOT_DOMAIN)
    show("USAGE_MESSAGE", "DE")
    show("USAGE_MESSAGE", "EN")
    show("DATA_NOT_FOUND", "DE")
    show("DATA_NOT_FOUND", "EN")

    print("\n=== Context: GLOBAL.DATABASE ===")
    set_language_context("GLOBAL.DATABASE")
    show("DATA_NOT_FOUND", "DE")  # should override GLOBAL
    show("DATA_NOT_FOUND", "EN")

    print("\n=== Context: GLOBAL.DATABASE.ORACLE ===")
    set_language_context("GLOBAL.DATABASE.ORACLE")
    show("DATA_NOT_FOUND", "DE")  # most specific override
    show("DATA_NOT_FOUND", "EN")

    print("\n=== Formatting example ===")
    set_language_context("GLOBAL.DATABASE.ORACLE")
    print(fmt("DB_ERROR", "DE", message="Timeout beim Verbinden"))
    print(fmt("DB_ERROR", "EN", message="Connection timeout"))

    # List catalogs
    from language_service import get_language
    cat = get_language()
    print("\nLabels in GLOBAL (direct):", ", ".join(cat.list_labels(domain=ROOT_DOMAIN)))
    print("Labels in GLOBAL.DATABASE (recursive):", ", ".join(cat.list_labels(domain="GLOBAL.DATABASE", recursive=True)))
    print("Languages for DATA_NOT_FOUND across domains:", ", ".join(cat.list_languages("DATA_NOT_FOUND")))
    print("Languages in GLOBAL.DATABASE.ORACLE (direct):", ", ".join(cat.list_languages(domain="GLOBAL.DATABASE.ORACLE")))

if __name__ == "__main__":
    main()