# language_service.py
# -*- coding: utf-8 -*-
"""
Global language service (singleton accessor) to make the LanguageCatalog
available application-wide without passing it around as a parameter.

Features:
- Domain-aware bootstrap (optionally loads domain JSON directly).
- Convenient helpers to switch context, change default language,
  and add more language files at runtime.
- Shortcuts `text()` and `fmt()` to retrieve/format messages.

Usage (domain-aware bootstrap):
    from language_service import init_language, text, fmt, set_language_context
    init_language(
        "messages.json",
        default_lang="DE",
        allowed_langs={"DE","EN"},
        context="GLOBAL",
        domain_aware=True
    )
    set_language_context("GLOBAL.DATABASE.ORACLE")
    print(text("DATA_NOT_FOUND"))
"""
from __future__ import annotations

from typing import Optional, Iterable
from language_catalog import LanguageCatalog

# Module-level singleton
_lang_catalog: Optional[LanguageCatalog] = None


def init_language(messages_path: str,
                  *,
                  default_lang: str = "EN",
                  allowed_langs: Optional[Iterable[str]] = None,
                  overwrite: bool = True,
                  context: Optional[str] = None,
                  domain_aware: bool = False) -> None:
    """
    Initialize the global LanguageCatalog once for the whole application.
    Safe to call multiple times; the last call wins.

    :param messages_path: Path to the JSON file with messages.
                          If domain_aware=True, the file must be domain-shaped:
                          {
                            "GLOBAL": { "LABEL": {"EN":"...", "DE":"..."} },
                            "GLOBAL.DATABASE.ORACLE": { ... }
                          }
                          Otherwise, legacy multi-language shapes are supported:
                          - object-of-objects { "LABEL": {"EN":"...", "DE":"..."} }
                          - list of records    [ {"label":"..","lang":"EN","text":".."}, ... ]
    :param default_lang: Default language code (e.g., "EN", "DE").
    :param allowed_langs: Optional iterable of allowed language codes.
    :param overwrite: When loading, replace existing entries on conflicts.
    :param context: Optional initial context/domain (e.g., "GLOBAL.CSV").
    :param domain_aware: If True, load with load_domains_from_file(); else load_from_file().
    """
    global _lang_catalog
    cat = LanguageCatalog(default_lang=default_lang, allowed_langs=allowed_langs)
    if domain_aware:
        cat.load_domains_from_file(messages_path, overwrite=overwrite)
    else:
        cat.load_from_file(messages_path, overwrite=overwrite)
    if context is not None:
        cat.set_context(context)
    _lang_catalog = cat


def get_language() -> LanguageCatalog:
    """
    Return the global LanguageCatalog instance.
    Raises RuntimeError if init_language() has not been called yet.
    """
    if _lang_catalog is None:
        raise RuntimeError("Language service not initialized. Call init_language(...) during app bootstrap.")
    return _lang_catalog


def set_language_context(domain: Optional[str]) -> None:
    """Set the current language context (domain)."""
    get_language().set_context(domain)


def set_default_language(lang: str) -> None:
    """Set the default language for the language catalog."""
    get_language().set_default_lang(lang)


def add_language_file(file_path: str, *, overwrite: bool = False) -> int:
    """
    Add a legacy multi-language file (GLOBAL domain).
    Returns the number of inserted/updated entries.
    """
    return get_language().add_file(file_path, overwrite=overwrite)


def add_domain_file(file_path: str, *, overwrite: bool = True) -> int:
    """
    Add a domain-aware language file (domain->label->lang->text).
    Returns the number of inserted/updated entries.
    """
    return get_language().load_domains_from_file(file_path, overwrite=overwrite)


def add_single_language_file(lang: str,
                             file_path: str,
                             *,
                             overwrite: bool = False,
                             domain: Optional[str] = None) -> int:
    """
    Add a single-language file (label->text or list of {label,text}) into a target domain.
    Returns the number of inserted/updated entries.
    """
    return get_language().load_language_only_from_file(lang, file_path, overwrite=overwrite, domain=domain)


def text(label: str,
         lang: Optional[str] = None,
         *,
         domain: Optional[str] = None,
         default: Optional[str] = None,
         fallback_lang: Optional[str] = None) -> str:
    """
    Retrieve a translated text for a label with hierarchical domain fallback.
    """
    return get_language().get_text(label, lang, domain=domain, default=default, fallback_lang=fallback_lang)


def fmt(label: str,
        lang: Optional[str] = None,
        *,
        domain: Optional[str] = None,
        default: Optional[str] = None,
        fallback_lang: Optional[str] = None,
        **kwargs) -> str:
    """
    Retrieve and format a translated text for a label using str.format(**kwargs),
    with hierarchical domain fallback.
    """
    return get_language().fmt(label, lang, domain=domain, default=default, fallback_lang=fallback_lang, **kwargs)