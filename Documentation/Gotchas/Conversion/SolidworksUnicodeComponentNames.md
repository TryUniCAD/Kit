# Unicode component names

## Expectation

An assembly's external component references resolve against adjacent files even when the
referenced name contains accented characters, and the writer can bundle those parts into a
self-contained output.

## Actual behavior

Assembly source paths come from Windows and are usually NFC, while some file systems
(macOS in particular) store names decomposed as NFD. Indexing only by
`name.casefold()` therefore missed `ADMISIÓN.SLDPRT` when the SLDASM stored `ADMISIÓN` in
NFC and the directory returned the NFD spelling. The reader reported
`sldasm.component_source_missing` for a file that was present, and the writer failed with
`external_requirements` when `allow_carrier=False`.

`ComponentFile` and `ResolvedPath` now normalize each name to NFC before casefolding on
both the index and lookup sides.

## Workaround

None needed after the fix. If a component still cannot be resolved, its file is genuinely
absent or renamed; the reader keeps the `sldasm.component_source_missing` diagnostic and
the writer still fails closed with `external_requirements`.

## Evidence

`TestASMNameNorm` writes an NFD-named `ADMISIÓN.SLDPRT` into a temporary directory,
indexes it, and resolves an NFC Windows path to that file.

A local audit of the 63-file V8 example corpus after the fix: 57 parts round-trip
`native-exact` and self-contained; `Cylinder Head Assy 1.SLDASM` (11 components, 240
mates) and `ENSAMBLE 3_IZQUIERDO.SLDASM` (12 components, 124 mates) now read with zero
missing components and write `native-template`, self-contained, application-usable, and
near-lossless. `Turbo Assy KF.SLDASM` and `Engine Assy KF EDIT 2.SLDASM` still report one
genuinely missing component, and `ENSAMBLAJE DE MOTOR V8.SLDASM` still fails to read
because a nested assembly source is absent.
