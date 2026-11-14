# Creo `DispDataTable` can use a compression variant the Unix-compress decoder rejects

## Expectation

Every compressed Creo PSB section starts with the Unix-compress magic `1f 9d` and decodes with the
same LZW state machine, so a section that starts with the magic is safe to inflate.

## Observed behavior

The `DispDataTable` section of a vendor-authored one-feature part starts with `1f 9d 10 e0 3b ...`.
The first nine-bit code is `480`, which is outside the initial 256-entry table, and the decoder raises
`Creo compression first code is invalid`.
The `DispDataTable` section of the vendor empty-part control starts with `1f 9d 10 e0 1e ...` and
decodes with the same decoder.

## Cause

The magic and the flags byte are not sufficient to identify the stream variant.
The ladder stream either uses a different initial dictionary or a different code-width schedule.
The current decoder assumes a 256-entry initial table and a nine-bit first code.

## Workaround

Treat a decode failure in a display-only section as a section warning, not a document failure.
The production reader skips the display-only section set (`DispDataTable`, `DispDataColor`,
`ModelView#*`, `THMB_IMG_*`, `ColorSchemeInfo*`, `CGF*`, `IndentTag`, `FeatRefData`, `AssMrgPrt`)
during strict validation, so a valid part with a display-section variant still reads.
Do not use `DispDataTable` as evidence that the feature or geometry sections are undecodable; those
sections are plain tagged streams in the same file.

## Evidence

- Ladder: `re/creo/oracle/ladder/ladder1.prt.2`, SHA-256
  `8de8280f17552caa406685845d6160195cb8b3a3d4e36fb5510c94a21d647762`.
- Control: `re/creo/oracle/empty/solid_start_part_mmks.prt`, SHA-256
  `b1374d7d356830300a8a4736b6f59a0ba5b5ef60938398a707fab02e69454aa`.
- Ladder body prefix: `1f9d10e03b56b8a44c1e7d143fbf7bde`.
- Control body prefix: `1f9d10e01ec573299effbe8d201314f32c`.

## Scope

This is a decoder-completeness gap for one display section.
It does not change the container, table-of-contents, or source-replay results.
