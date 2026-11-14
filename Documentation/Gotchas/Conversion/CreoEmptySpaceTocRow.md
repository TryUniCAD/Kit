# Creo table of contents can contain an `EMPTY_SPACE_FOR_REUSE` row

## Expectation

Every `#UGC_TOC` row names a section whose extent starts with `#<name>` and whose offset and length
are valid.

## Observed behavior

The vendor empty-part control contains a row named `EMPTY_SPACE_FOR_REUSE`.
Its extent does not start with `#EMPTY_SPACE_FOR_REUSE`, so a strict reader raises
`Creo table row 'EMPTY_SPACE_FOR_REUSE' has an invalid extent` and rejects a valid part.

## Cause

`EMPTY_SPACE_FOR_REUSE` is a free-space marker, not a section.
It records reusable space in the file, and the loader skips it.

## Workaround

Skip `EMPTY_SPACE_FOR_REUSE` rows the same way the reader already skips `NEXT_TOC_ENTRY`.
Do not treat the row as a section and do not fail the document on it.

## Evidence

- Control: `re/creo/oracle/empty/solid_start_part_mmks.prt`, SHA-256
  `b1374d7d356830300a8a4736b6f59a0ba5b5ef60938398a707fab02e69454aa`.
- Before the fix, `ReadDocument` raised on the row in default strict mode.
- After the fix, the control reads with 52 sections and only the `creo.container_only` diagnostic.

## Scope

This is a table-of-contents marker, not a model record.
It does not change the section grammar or the source-replay result.
