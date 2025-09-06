# Requirements Document – Language Module (`language_catalog`)

## Purpose
The Language Module provides a centralized way to manage all user-facing texts of the application. Instead of hardcoding strings inside the code, texts are referenced via **labels** and loaded dynamically for multiple languages (e.g. English `EN`, German `DE`). This enables:

- **Central text management**: easy maintenance of messages, usage notes, errors.  
- **Multi-language support**: same labels, multiple languages.  
- **Consistency**: the same label always maps to the same text across the project.  
- **Flexibility**: texts can be loaded from JSON files, set dynamically, and exported again.

---

## Functional Requirements

### 1. Storage Structure
- Texts must be stored internally in a structure like:
  ```json
  {
    "LABEL": {
      "EN": "English text",
      "DE": "German text"
    }
  }

	•	Labels are case-sensitive strings.
	•	Language codes must always be stored in uppercase (e.g. EN, DE, FR).

2. Managing Entries
	•	Add/Update (set)
A method set_text(label, lang, text, overwrite=True) must allow inserting or updating a text for a given (label, lang).
	•	overwrite=False prevents overwriting an existing entry.
	•	Retrieve (get)
A method get_text(label, lang, fallback_lang=None, default=None) must return the text in the requested language.
	•	If missing, it must fall back to fallback_lang.
	•	If still missing, it must fall back to the module’s default_lang.
	•	If nothing is found, it must return default (if provided) or raise an error.

3. String Formatting
	•	Texts may contain placeholders (e.g. "Unknown query label: {q_label} dear {user}").
	•	A method fmt(label, lang, **kwargs) must retrieve the text and apply Python’s str.format(**kwargs).
	•	Example:
	•	Text: "Unknown query label: {q_label} dear {user}"
	•	Call: fmt("UNKNOWN_QUERY_LABEL", "EN", q_label="FOO", user="Alice")
	•	Result: "Unknown query label: FOO dear Alice"

4. Default Language
	•	The module must have a configurable default_lang (e.g. "EN").
	•	If lang=None is passed to get_text or fmt, it should automatically use the default language.
	•	A method set_default_lang(lang) must allow changing this default at runtime.

5. Language Restrictions
	•	Optionally, a set of allowed_langs may be passed to the constructor.
	•	If given, all language codes must be validated against this set.
	•	If a text is set for a language not in the allowed set, an error must be raised.

6. Listing Functions
	•	list_labels() → must return a sorted list of all available labels.
	•	list_languages(label=None) → must return available languages.
	•	If label=None, return the union of all languages across all labels.
	•	If label="X", return only languages available for that label.

7. Import / Export
	•	Load from file
	•	load_from_file(path, overwrite=True) must read a JSON file and add entries.
	•	It must support two JSON formats:
Object of objects:

{
  "USAGE_MESSAGE": {
    "EN": "Usage...",
    "DE": "Verwendung..."
  }
}

List of records:

[
  {"label": "USAGE_MESSAGE", "lang": "EN", "text": "Usage..."},
  {"label": "USAGE_MESSAGE", "lang": "DE", "text": "Verwendung..."}
]


	•	Reload from file
	•	reload_from_file(path) must clear all current entries and load from the given file.
	•	Export
	•	to_dict() must export the internal structure as Dict[str, Dict[str, str]].

⸻

Non-Functional Requirements
	•	Encoding: All files must be UTF-8.
	•	Error handling: Invalid JSON structures, missing labels, or invalid language codes must raise clear ValueError or KeyError messages.
	•	Extensibility: New languages or labels must be addable without code changes.
	•	Thread safety: Each thread/request may use its own instance of the catalog.

⸻

Example Usage

Example JSON file (messages.json)

{
  "USAGE_MESSAGE": {
    "EN": "Usage: python export_oracle_to_csv.py <query_label> [csv_config_label]",
    "DE": "Verwendung: python export_oracle_to_csv.py <query_label> [csv_config_label]"
  },
  "UNKNOWN_QUERY_LABEL": {
    "EN": "Unknown query label: {q_label} dear {user}",
    "DE": "Unbekanntes Query-Label: {q_label} lieber {user}"
  },
  "DB_ERROR": {
    "EN": "Database error {code}: {message}",
    "DE": "Datenbankfehler {code}: {message}"
  }
}

Example Code

from language_catalog import LanguageCatalog

# Initialize with default language DE and allowed languages
langcat = LanguageCatalog(default_lang="DE", allowed_langs={"EN", "DE"})

# Load texts from file
langcat.load_from_file("messages.json")

# Simple retrieval
print(langcat.get_text("USAGE_MESSAGE", "EN"))
# -> "Usage: python export_oracle_to_csv.py <query_label> [csv_config_label]"

# Default language retrieval (DE)
print(langcat.get_text("USAGE_MESSAGE"))
# -> "Verwendung: python export_oracle_to_csv.py <query_label> [csv_config_label]"

# String formatting with multiple variables
print(langcat.fmt("UNKNOWN_QUERY_LABEL", "EN", q_label="LPIS", user="Alice"))
# -> "Unknown query label: LPIS dear Alice"

print(langcat.fmt("DB_ERROR", "DE", code=1017, message="Invalid username/password"))
# -> "Datenbankfehler 1017: Invalid username/password"


⸻

Acceptance Criteria
	•	All specified functions (set_text, get_text, fmt, list_labels, list_languages, load_from_file, reload_from_file, to_dict) must exist and behave as described.
	•	The module must handle both JSON input formats.
	•	The system must support at least two languages (EN, DE) and allow future expansion.
	•	Placeholders in texts must be replaceable with multiple parameters via .fmt.
	•	The module must raise clear errors for invalid usage (e.g. unknown label without default).

---

