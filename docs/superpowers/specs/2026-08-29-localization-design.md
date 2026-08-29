# Monokular Localization (i18n) — Design

Date: 2026-08-29
Status: proposed
Target release: 1.1.0

## Goal

Ship Monokular in the same 25 languages as Dyedfox Radio, using Qt's
Linguist toolchain, with terminology that matches each language's
established desktop conventions rather than literal translation.

## Languages

The set is taken verbatim from `dyedfox-radio/translations/`:

```
bg ca cs da de el es et fi fr hr hu it lt lv nb nl pl pt ro sk sl sr sv uk
```

25 locales. English is the source language and ships no `.ts` file.

## How translations load

`main.py` gains a loader that mirrors Dyedfox Radio's, extended with the
same path-candidate pattern `_find_icon()` already uses, because
Monokular is installed to `/usr/lib/monokular` and also ships as a
PyInstaller bundle:

```python
def _find_translations_dir() -> str:
    candidates = [
        os.path.join(getattr(sys, "_MEIPASS", ""), "translations"),
        os.path.join(os.path.dirname(__file__), "translations"),
        "/usr/lib/monokular/translations",
    ]
    ...
```

At startup the app reads `QLocale.system().name()` (e.g. `uk_UA`) and
asks `QTranslator.load()` for `monokular_uk_UA`, which falls back to
`monokular_uk` on its own. If nothing matches, the UI stays English.

There is no in-app language selector — matching Radio, and matching the
answer given during brainstorming.

## What gets translated

Every user-visible string in `app/main_window.py`,
`app/thumbnail_grid.py`, `app/preview_dialog.py`, `app/export_dialog.py`
and `app/settings_dialog.py` is wrapped in `self.tr(...)`. That is
roughly 60 source strings.

### What deliberately stays untranslated

- **`Monokular`** — the product name, including in the window title.
- **Format labels** (`PNG`, `JPEG`, `WEBP`, `TIFF`, `PDF`) — these are
  persisted into QSettings under `export/format` and looked up by
  `find_format()`. Translating them would break every saved setting the
  moment a user changed locale. They are proper nouns anyway.
- **Symbol buttons** (`◀ ▶ − + ↺ ↻ ▲ 🔍− 🔍+`) — the glyph is the
  control. Their *tooltips* are translated.
- **File-dialog glob patterns** (`*.pdf`), settings keys, and stylesheets.

### Output-mode combo — a fix this work forces

`settings_dialog.py` currently puts the raw storage keys
`same_as_pdf` / `last_used` / `fixed` straight into a combo box, so the
user already reads database values in the UI. Translating that as-is
would be nonsense. The combo will show translated labels carried by
`QComboBox.addItem(label, userData=key)` and save `currentData()`, the
same pattern the thumbnail-size combo beside it already uses. The stored
values are unchanged, so existing configs keep working.

## Plurals

Three strings vary with a count, and Slavic and Baltic languages in this
set need three plural forms, not two. Each uses Qt's numerus form so
Linguist generates the right number of slots per language:

| Location | Source string |
|---|---|
| `export_dialog.py` | `Exported %n page(s) to:` |
| `export_dialog.py` | `%n page(s) selected` |
| `main_window.py` | `Selected (%n): pages %1` |

`self.tr(source, "", n)` selects the form; `%1` carries the page list.

## Terminology

Shared strings reuse the exact wording already shipped in Dyedfox Radio,
so the two apps read as one family:

| Source | de | fr | pl | uk | es | it |
|---|---|---|---|---|---|---|
| Settings | Einstellungen | Paramètres | Ustawienia | Параметри | Configuración | Impostazioni |
| About | Über | À propos | O programie | Про застосунок | Acerca de | Informazioni |

Monokular-specific vocabulary follows each platform's established term
rather than a literal rendering — e.g. *Export* is `Exportieren` (de),
`Eksportuj` (pl), `Експортувати` (uk); *Thumbnail* is `Miniaturansicht`
(de), `Miniatura` (pl/es/it), `Мініатюра` (uk); *Zero padding* is
rendered as "leading zeros" in every language, since the English is
jargon.

## Toolchain

Both tools are already installed on this machine; nothing new is needed.

- `pylupdate6` (from `python-pyqt6`) refreshes the `.ts` files from
  source. My earlier note that `lrelease` was missing was wrong — it is
  present as **`lrelease6`** (from `qt6-tools`).
- `lrelease6` compiles each `.ts` into the `.qm` the app loads.

Both `.ts` and `.qm` are committed, as in Radio, so neither building the
package nor installing from the AUR requires Qt's dev tools.

`translations/TRANSLATING.md` documents both flows for contributors,
mirroring Radio's.

## Packaging

- **PKGBUILD** — install `translations/*.qm` into
  `/usr/lib/monokular/translations/`. `qt6-tools` is *not* added as a
  dependency, because the compiled `.qm` files are committed.
- **monokular.spec** — add `(translations/*.qm, 'translations')` to
  `datas` so the PyInstaller bundle carries them.

## Testing

Automated, in `tests/test_translations.py`:

- every language in the list has both a `.ts` and a compiled `.qm`
- no `.ts` contains a `type="unfinished"` translation
- every `.ts` message has a non-empty translation
- the numerus strings carry the full number of plural forms each
  language requires
- the loader resolves `uk_UA` to the `uk` catalogue and returns cleanly
  for an unknown locale
- a smoke test that installing a translator actually changes a known
  window title away from its English source

Manual: launch under `LANG=de_DE.UTF-8` and `LANG=uk_UA.UTF-8` and
screenshot the main window, settings and export dialogs to confirm no
layout breaks or clipped labels.

## Ordering

Strings are stable now that features 1–4 have landed, so `pylupdate6`
runs once against final source. Sequence: wrap strings → fix the
output-mode combo → generate `.ts` → translate → compile `.qm` → loader
→ packaging → tests.

## Out of scope

- In-app language switching
- Right-to-left languages (none in the set)
- Translating the README or the desktop file's `Comment=`
