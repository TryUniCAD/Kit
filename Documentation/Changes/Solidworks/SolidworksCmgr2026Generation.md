# Generation-2026 configuration manager

## Behavior

`Contents/CMgr` now has an independent generation-19000 encoder for one native feature atom alongside the unchanged generation-18000 default. The public `Generation` and optional `Build` arguments select the 2026 grammar and its neutral build tag.

The 2026 writer preserves the existing archive graph and computed object/class references. It removes the old 104-byte gated RV symbol group, emits neutral DSPBR properties, updates appearance scalars and display-state metadata, adds one linked-null reference, and appends the zero variable-table presence flag. It constructs these records through typed primitive/string functions rather than embedding or reading vendor streams.

The scope is deliberately limited to a single feature atom. The encoder rejects other atom counts and other document generations rather than extrapolating unverified history or assembly behavior.

## Configuration

The existing `Build` argument is optional. When it is omitted, the encoder chooses generation 18000 with build 2025268 or generation 19000 with build 2026306. Existing 2025 callers and public keyword spellings retain their prior default bytes.

`src/convert/adapters/solidworks/container/Cmgr2026.py` contains the independent appearance and tail records. `Cmgr.py` performs generation validation and dispatch without invoking CAD software in production.

## Verification

The public `encode_cmgr_stream(Generation=19000)` entry point produces 2,159 bytes, replacing the legacy 1,957-byte `CMgr` for the same one-feature inputs. The 300-byte DSPBR record, visual prefix, scalar tail, identity block, linked null, and closing flag are independently typed and length-checked.

A fresh native file using this `CMgr`, an independently constructed 2026 `Definition`, and a comparison-control `Config-0` passed SOLIDWORKS 34.5.2:

- open and rebuild succeeded with zero load errors or warnings;
- one body, 9,189 mm³, 3,173.38914944295 mm²;
- `D1@Boss-Extrude1` remained 9 mm;
- an unsaved edit to 17 mm rebuilt to 17,357 mm³ and 4,179.06839339223 mm² before closing without saving.

The independently generated 2026 `Config-0` completes this single-feature family. Fresh public `write_document(..., allow_carrier=False)` files pass open and rebuild with one body: 9,189 mm³ at 9 mm depth and 58,830 mm³ for an independently shifted profile at 37 mm. `Sketch1` and `Boss-Extrude1` remain native, and an unsaved live edit of the shifted part to 17 mm rebuilds to 27,030 mm³ and 5,822.57851076441 mm².

The next higher-profile 1.1 display extent uses the computed visual growth delta when inserting later gates; it must not reuse pre-growth offsets. The new offset invariant is covered by the public writer's fresh oracle output, not by comparison-control substitution.

This is bounded single-feature evidence, not complete SLDPRT, SLDASM, or SLDDRW support. Other histories, atom counts, assemblies, drawings, and arbitrary feature families remain outside the recovered contract and fail closed where unsupported.

Local formatting, Ruff, mypy, pyright, and repository steering checks passed. Unit/integration suites were not run locally; remote PR CI owns those checks.

## Linked information

- [Document-generation skew gotcha](../../Gotchas/Conversion/SolidworksDocumentGenerationSkew.md)
- [Five-line native histories](SolidworksFiveLineNativeHistories.md)
