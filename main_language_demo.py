# main_language_demo.py
# -*- coding: utf-8 -*-
"""
Minimal wiring example for LanguageCatalog usage.
"""
from language_catalog import LanguageCatalog

def main() -> None:
    # Initialize catalog with default language and allowed set
    langcat = LanguageCatalog(default_lang="DE", allowed_langs={"DE", "EN"})
    # Load messages from file
    langcat.load_from_file("messages.json", overwrite=True)

    # Show usage in default language (DE)
    print(langcat.get_text("USAGE_MESSAGE", None))  # None -> use default DE

    # Show usage in EN
    print(langcat.get_text("USAGE_MESSAGE", "EN"))

    # Format an error message in DE
    print(langcat.fmt("UNKNOWN_QUERY_LABEL", "DE", q_label="FOO_LABEL", user="Alice"))

    # List catalogs
    print("Labels:", ", ".join(langcat.list_labels()))
    print("Languages:", ", ".join(langcat.list_languages()))
    print("Languages for USAGE_MESSAGE:", ", ".join(langcat.list_languages("USAGE_MESSAGE")))

if __name__ == "__main__":
    main()