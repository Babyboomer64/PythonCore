# language_catalog.py
# -*- coding: utf-8 -*-
"""
language_catalog.py
Centralized language/text catalog for application messages with:
- default_lang + allowed_langs
- setters/getters, catalogs, formatting
- loading from JSON (multi-language & single-language)
- additive "add_file" loader
- HIERARCHICAL DOMAINS / CONTEXT (e.g., GLOBAL.DATABASE.ORACLE with parent fallback)

Domain rules:
- Domains are dot-separated paths, e.g. "GLOBAL.DATABASE.ORACLE".
- Lookups start in the most specific domain and walk up the tree to its parents,
  finally falling back to the root domain "GLOBAL".
- Legacy JSON files without any domain information are stored under domain "GLOBAL",
  so existing data remains fully compatible.

Examples of search order for label=DATA_NOT_FOUND in domain "GLOBAL.DATABASE.ORACLE":
  GLOBAL.DATABASE.ORACLE -> GLOBAL.DATABASE -> GLOBAL
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Optional, Iterable, List


# --------------------------- Domain utilities ---------------------------------
ROOT_DOMAIN = "GLOBAL"


def _normalize_domain(domain: Optional[str]) -> str:
    """Normalize a domain string; None/empty becomes ROOT_DOMAIN."""
    if not domain:
        return ROOT_DOMAIN
    d = domain.strip()
    return d if d else ROOT_DOMAIN


def _domain_chain(domain: str) -> List[str]:
    """
    Build a search chain from most specific domain to ROOT_DOMAIN.
    Example: "GLOBAL.DATABASE.ORACLE" -> ["GLOBAL.DATABASE.ORACLE", "GLOBAL.DATABASE", "GLOBAL"]
    If domain already equals ROOT_DOMAIN, returns ["GLOBAL"].
    """
    domain = _normalize_domain(domain)
    if domain == ROOT_DOMAIN:
        return [ROOT_DOMAIN]
    parts = domain.split(".")
    out = [".".join(parts[:i]) for i in range(len(parts), 0, -1)]
    # Ensure ROOT_DOMAIN is included at the end (if not already)
    if out[-1] != ROOT_DOMAIN:
        out.append(ROOT_DOMAIN)
    return out


class LanguageCatalog:
    def __init__(
        self,
        default_lang: str = "EN",
        allowed_langs: Optional[Iterable[str]] = None
    ) -> None:
        # Internal structure: { domain: { label: { lang: text, ... }, ... }, ... }
        self._data: Dict[str, Dict[str, Dict[str, str]]] = {}
        self._default_lang = default_lang.upper() if default_lang else "EN"
        self._allowed = {s.upper() for s in allowed_langs} if allowed_langs else None
        # Current context domain (affects methods when domain is omitted)
        self._context_domain: str = ROOT_DOMAIN

    # ----------------------------- defaults & context --------------------------
    @property
    def default_lang(self) -> str:
        """Return the current default language code."""
        return self._default_lang

    def set_default_lang(self, lang: str) -> None:
        """Set the default language code (validated against allowed_langs if present)."""
        code = self._normalize_lang(lang)
        self._default_lang = code

    @property
    def context(self) -> str:
        """Return current context domain."""
        return self._context_domain

    def set_context(self, domain: Optional[str]) -> None:
        """Set current context domain (None/empty -> GLOBAL)."""
        self._context_domain = _normalize_domain(domain)

    # --------------------------- setters / getters ----------------------------
    def set_text(
        self,
        label: str,
        lang: str,
        text: str,
        *,
        overwrite: bool = True,
        domain: Optional[str] = None,
    ) -> None:
        """
        Insert or update a text for (domain, label, lang).
        If domain is omitted, the current context domain is used.
        """
        if not label or not isinstance(label, str):
            raise ValueError("label must be a non-empty string.")
        code = self._normalize_lang(lang)
        if not isinstance(text, str):
            raise ValueError("text must be a string.")
        dom = _normalize_domain(domain or self._context_domain)
        bucket_labels = self._data.setdefault(dom, {})
        bucket_langs = bucket_labels.setdefault(label, {})
        if not overwrite and code in bucket_langs:
            return
        bucket_langs[code] = text

    def get_text(
        self,
        label: str,
        lang: Optional[str] = None,
        *,
        fallback_lang: Optional[str] = None,
        default: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> str:
        """
        Retrieve a text for (domain, label, lang) with hierarchical domain fallback.
        Resolution order per domain step:
          1) explicit lang (or catalog default_lang if None)
          2) fallback_lang (explicit)
          3) catalog default_lang (if not already used)
        Domains are searched from most specific to ROOT_DOMAIN.

        Raises KeyError if nothing found and default is None.
        """
        if not label:
            if default is not None:
                return default
            raise KeyError("Missing label")

        dom = _normalize_domain(domain or self._context_domain)
        chain = _domain_chain(dom)

        # precompute language order for each step
        primary_lang = self._normalize_lang(lang) if lang else self._default_lang
        fallback_code = self._normalize_lang(fallback_lang) if fallback_lang else None

        for d in chain:
            labels = self._data.get(d)
            if not labels:
                continue
            langs = labels.get(label)
            if not langs:
                continue

            tried = set()
            # 1) explicit or default_lang
            tried.add(primary_lang)
            if primary_lang in langs:
                return langs[primary_lang]

            # 2) explicit fallback_lang
            if fallback_code:
                tried.add(fallback_code)
                if fallback_code in langs:
                    return langs[fallback_code]

            # 3) catalog default_lang (if different)
            if self._default_lang not in tried and self._default_lang in langs:
                return langs[self._default_lang]

        if default is not None:
            return default
        raise KeyError(f"Text not found for label={label!r} in domain chain {chain}")

    def fmt(
        self,
        label: str,
        lang: Optional[str] = None,
        *,
        fallback_lang: Optional[str] = None,
        default: Optional[str] = None,
        domain: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Retrieve and format a text using Python str.format(**kwargs) with domain fallback."""
        template = self.get_text(
            label,
            lang,
            fallback_lang=fallback_lang,
            default=default,
            domain=domain,
        )
        try:
            return template.format(**kwargs)
        except Exception:
            return template  # do not mask issues—return template as-is

    # -------------------------------- introspection ----------------------------
    def has_text(
        self,
        label: str,
        lang: Optional[str] = None,
        *,
        domain: Optional[str] = None,
        recursive: bool = True
    ) -> bool:
        """
        Return True if a text exists for the given label under the given domain context.

        :param label: message label to check (non-empty).
        :param lang: if provided, check for that language only; otherwise check for any language.
        :param domain: starting domain (defaults to current context domain).
        :param recursive: if True, walk the domain chain (e.g., GLOBAL.DATABASE.ORACLE -> ... -> GLOBAL);
                          if False, only check the exact domain.
        """
        if not label or not isinstance(label, str):
            return False

        dom = _normalize_domain(domain or self._context_domain)
        domains = _domain_chain(dom) if recursive else [dom]
        code = self._normalize_lang(lang) if lang else None

        for d in domains:
            labels = self._data.get(d)
            if not labels:
                continue
            lang_map = labels.get(label)
            if not lang_map:
                continue
            if code:
                if code in lang_map:
                    return True
            else:
                # any language present for this label in this domain
                if bool(lang_map):
                    return True
        return False

    # -------------------------------- catalogs --------------------------------
    def list_labels(self, *, domain: Optional[str] = None, recursive: bool = False) -> list[str]:
        """
        Return a sorted list of available labels.
        - If domain is None: union across all domains.
        - If domain is given:
            - recursive=False: labels directly in this domain
            - recursive=True: union across this domain and all its descendants
        """
        if domain is None:
            labels = set()
            for labels_map in self._data.values():
                labels.update(labels_map.keys())
            return sorted(labels)

        dom = _normalize_domain(domain)
        if not recursive:
            return sorted(self._data.get(dom, {}).keys())

        # recursive: include subdomains (prefix match "dom.")
        labels = set(self._data.get(dom, {}).keys())
        prefix = dom + "."
        for d, labels_map in self._data.items():
            if d.startswith(prefix):
                labels.update(labels_map.keys())
        return sorted(labels)

    def list_languages(
        self,
        label: Optional[str] = None,
        *,
        domain: Optional[str] = None,
        recursive: bool = False
    ) -> list[str]:
        """
        Return a sorted list of languages.
        - If label is None and domain is None: union of all languages across all labels/domains.
        - If label is None and domain is set:
            - recursive=False: languages present directly under that domain
            - recursive=True: languages across domain and all its subdomains
        - If label is set:
            - domain=None: union of languages for that label across all domains
            - domain set:
                - recursive=False: languages for that label directly in that domain
                - recursive=True: languages for that label across domain + subdomains
        """
        langs = set()
        if label is None and domain is None:
            for labels_map in self._data.values():
                for lang_map in labels_map.values():
                    langs.update(lang_map.keys())
            return sorted(langs)

        if label is None and domain is not None:
            dom = _normalize_domain(domain)
            if not recursive:
                labels_map = self._data.get(dom, {})
                for lang_map in labels_map.values():
                    langs.update(lang_map.keys())
                return sorted(langs)
            # recursive
            prefix = dom + "."
            for d, labels_map in self._data.items():
                if d == dom or d.startswith(prefix):
                    for lang_map in labels_map.values():
                        langs.update(lang_map.keys())
            return sorted(langs)

        # label is set
        if domain is None:
            for labels_map in self._data.values():
                if label in labels_map:
                    langs.update(labels_map[label].keys())
            return sorted(langs)

        dom = _normalize_domain(domain)
        if not recursive:
            lang_map = self._data.get(dom, {}).get(label, {})
            langs.update(lang_map.keys())
            return sorted(langs)

        prefix = dom + "."
        for d, labels_map in self._data.items():
            if d == dom or d.startswith(prefix):
                if label in labels_map:
                    langs.update(labels_map[label].keys())
        return sorted(langs)

    # --------------------------------- loaders --------------------------------
    def add_file(self, file_path: str | Path, *, overwrite: bool = False) -> int:
        """
        Convenience method to load an additional multi-language JSON file and merge
        it into the GLOBAL domain (legacy format). By default, it does not overwrite
        existing entries; set overwrite=True to replace them.
        """
        return self.load_from_file(file_path, overwrite=overwrite)

    def load_from_file(self, file_path: str | Path, *, overwrite: bool = True) -> int:
        """
        Load texts from a JSON file (legacy multi-language) into the GLOBAL domain.
        Supports two shapes:
          - object-of-objects: { "LABEL": {"EN": "...", "DE": "..."} }
          - list of records:   [ {"label": "...", "lang": "EN", "text": "..."}, ... ]
        Returns the number of inserted/updated entries.
        """
        data = self._load_json(file_path)
        count = 0

        if isinstance(data, dict):
            # object-of-objects (GLOBAL domain)
            for label, mapping in data.items():
                if not isinstance(mapping, dict):
                    raise ValueError(f"Invalid entry for label {label!r}: expected object of languages.")
                for lang, text in mapping.items():
                    self.set_text(label, lang, text, overwrite=overwrite, domain=ROOT_DOMAIN)
                    count += 1

        elif isinstance(data, list):
            # list of records
            for rec in data:
                if not isinstance(rec, dict):
                    raise ValueError("List form expects objects with keys: label, lang, text.")
                label = rec.get("label")
                lang = rec.get("lang")
                text = rec.get("text")
                if not isinstance(label, str) or not isinstance(lang, str) or not isinstance(text, str):
                    raise ValueError("Each record must have string fields: label, lang, text.")
                self.set_text(label, lang, text, overwrite=overwrite, domain=ROOT_DOMAIN)
                count += 1
        else:
            raise ValueError("JSON must be an object or a list.")

        return count

    def load_domains_from_file(self, file_path: str | Path, *, overwrite: bool = True) -> int:
        """
        Load a domain-aware JSON file:
        {
          "GLOBAL": {
            "LABEL": { "EN": "...", "DE": "..." }
          },
          "GLOBAL.DATABASE.ORACLE": {
            "LABEL": { "EN": "...", "DE": "..." }
          }
        }
        Returns number of inserted/updated entries.
        """
        data = self._load_json(file_path)
        if not isinstance(data, dict):
            raise ValueError("Domain-aware JSON must be a top-level object.")
        count = 0
        for dom, labels in data.items():
            if not isinstance(dom, str) or not isinstance(labels, dict):
                raise ValueError("Each domain key must map to an object of labels.")
            dom_norm = _normalize_domain(dom)
            for label, lang_map in labels.items():
                if not isinstance(label, str) or not isinstance(lang_map, dict):
                    raise ValueError("Each label must map to an object of languages.")
                for lang, text in lang_map.items():
                    if not isinstance(lang, str) or not isinstance(text, str):
                        raise ValueError("Languages must map to string texts.")
                    self.set_text(label, lang, text, overwrite=overwrite, domain=dom_norm)
                    count += 1
        return count

    def load_language_only_from_file(
        self,
        lang: str,
        file_path: str | Path,
        *,
        overwrite: bool = False,
        domain: Optional[str] = None,
    ) -> int:
        """
        Load a single-language JSON file and insert texts under the given language code
        and target domain (default: GLOBAL). Supported JSON shapes:
          - object: { "LABEL": "Text", ... }
          - list:   [ {"label": "LABEL", "text": "Text"}, ... ]
        """
        code = self._normalize_lang(lang)
        tgt_domain = _normalize_domain(domain)
        data = self._load_json(file_path)
        count = 0

        if isinstance(data, dict):
            for label, text in data.items():
                if not isinstance(label, str) or not isinstance(text, str):
                    raise ValueError("Single-language JSON must map str labels to str texts.")
                self.set_text(label, code, text, overwrite=overwrite, domain=tgt_domain)
                count += 1
        elif isinstance(data, list):
            for rec in data:
                if not isinstance(rec, dict):
                    raise ValueError("List form expects objects with keys: label, text.")
                label = rec.get("label")
                text = rec.get("text")
                if not isinstance(label, str) or not isinstance(text, str):
                    raise ValueError("Each record must have string fields: label, text.")
                self.set_text(label, code, text, overwrite=overwrite, domain=tgt_domain)
                count += 1
        else:
            raise ValueError("JSON must be an object or a list.")

        return count

    def reload_from_file(self, file_path: str | Path) -> int:
        """
        Clear the current catalog and load from the given legacy multi-language file
        into GLOBAL domain. Returns number of entries loaded.
        """
        self._data.clear()
        return self.load_from_file(file_path, overwrite=True)

    # -------------------------------- internals --------------------------------
    def _normalize_lang(self, lang: str) -> str:
        if not lang or not isinstance(lang, str):
            raise ValueError("lang must be a non-empty string.")
        code = lang.upper()
        if self._allowed is not None and code not in self._allowed:
            raise ValueError(f"lang {code!r} not in allowed set {sorted(self._allowed)}")
        return code

    @staticmethod
    def _load_json(file_path: str | Path) -> Any:
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {p}")
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)

    # -------------------------------- utilities --------------------------------
    def to_dict(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Export the current catalog as domain->label->lang->text dictionary."""
        # Shallow copies to avoid external mutation
        return {dom: {lbl: dict(lang_map) for lbl, lang_map in labels.items()}
                for dom, labels in self._data.items()}