# Translating Monokular

Translations use the Qt Linguist format (`.ts` for sources, `.qm` for the
compiled catalogues the app loads). Both are committed, so Monokular runs
from a source checkout without Qt's development tools. The Arch package
recompiles the `.qm` from the `.ts` at build time (`qt6-tools` is a
makedepend), so the shipped catalogues always match the sources in the tag.

## Adding a new language

1. Copy `monokular_uk.ts` to `monokular_<locale>.ts`
   (e.g. `monokular_de.ts` for German).
2. Set the `language` attribute on the `<TS>` tag to the target locale,
   e.g. `language="de_DE"`. Getting this right matters: it tells
   `lrelease` how many plural forms the language needs.
3. Fill in every `<translation>` element.
4. Compile it and check that the tool reports no warnings:

   ```
   lrelease6 monokular_<locale>.ts
   ```

5. Add the locale to `LANGUAGES` in `app/i18n.py`.
6. Submit a pull request — thank you!

## Plural forms

Three strings vary with a count and use Qt's `%n` placeholder:

- `%n page(s) selected`
- `Exported %n page(s) to:`
- `Selected (%n): pages {0}`

Each needs one `<numerusform>` per plural form your language has — one
for Hungarian, two for German or Spanish, three for Polish, Czech or
Ukrainian, four for Slovene. `lrelease6` warns if the count is wrong;
`tests/test_translations.py` fails the build on that warning.

`{0}` is substituted by Python and must survive translation unchanged.

## Updating strings after a code change (developers)

Run `pylupdate6` from the project root:

```
pylupdate6 \
    app/main_window.py app/thumbnail_grid.py app/preview_dialog.py \
    app/export_dialog.py app/settings_dialog.py \
    -ts translations/monokular_uk.ts
```

Existing translations are preserved; new source strings arrive marked
`type="unfinished"`. Repeat for each locale, translate the new entries,
then recompile:

```
lrelease6 translations/monokular_*.ts
```

## How the app loads translations (developers)

`app/i18n.py` reads the system locale (e.g. `uk_UA`) at startup and asks
`QTranslator` for `monokular_uk_UA`, which narrows to `monokular_uk` on
its own. Catalogues are looked up in the PyInstaller bundle, then beside
the source tree, then in `/usr/lib/monokular/translations`. If none
matches, the interface stays in English.

Format names (`PNG`, `JPEG`, `WEBP`, `TIFF`, `PDF`) are deliberately not
translated: they are stored in the user's settings file and looked up by
name.
