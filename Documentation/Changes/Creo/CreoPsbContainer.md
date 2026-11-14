# Creo PSB container reader and source replay

## Change

Adds the `creo.prt` adapter for PTC Creo Parametric and Pro/ENGINEER PSB part files.

The reader validates the `#UGC:2` header, reads the fixed-width table of contents, follows continuation tables, validates section extents, inflates Unix-compress sections, extracts the native JPEG thumbnail, and retains the source bytes for exact replay.

The writer emits the retained source bytes only when the source digest still matches. It refuses independent PSB synthesis.

## Use

```python
from convert import open_document, write_document

DocumentValue = open_document("bracket.prt")
ResultValue = write_document(DocumentValue, "bracket-copy.prt")
```

The result reports `mode="exact_native_roundtrip"` and keeps `vendor_loadable` and `application_usable` false because this change does not measure a new native model.

## Limits

- Native geometry, topology, sketches, dimensions, constraints, and feature records are inventoried but not decoded into neutral records.
- The reader reports no bodies and no feature timeline.
- The writer is source replay, not an independent writer.
- The adapter does not claim lossless cross-format translation or parametric authoring.
- The adapter does not use a CAD application at runtime.

## Verification

- The container grammar was checked against a Creo 2027.2 empty-part control, two public Ender-3 parts, and the public cadmpeg and TeamCraft format descriptions.
- Local Creo 2027.2 opened the empty-part control in a fresh session.
- A hand-built legacy ASCII part was rejected by Creo 2027.2, so no legacy writer path is claimed.
- Remote integration coverage builds a synthetic PSB file, reads its header, table, thumbnail, and source bytes, and verifies exact replay.
- No vendor file, vendor block, or captured table is stored under `src/` or in the test fixture.

## Documentation

- [Creo adapter](../../Reference/Adapters/Creo.md)
- [Container findings](../../../re/creo/container/Container.md)
- [Data model](../../../re/creo/data-model/DataModel.md)
- [Oracle notes](../../../re/creo/oracle/Oracle.md)
- [Writer gap](../../../re/creo/open-items/WriterGap.md)
- [ARM64 startup gotcha](../../Gotchas/Conversion/CreoArmStartup.md)
- [Legacy ASCII rejection gotcha](../../Gotchas/Conversion/CreoLegacyAsciiRejected.md)
