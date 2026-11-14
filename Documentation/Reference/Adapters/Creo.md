# Creo adapter

## Purpose and scope

The `creo.prt` adapter reads PTC Creo Parametric and Pro/ENGINEER PSB part files.
It validates the container, lists sections, inflates compressed sections, extracts the native thumbnail, and retains the source bytes for exact replay.
It does not decode native geometry or feature records into neutral records.

## Container

A PSB file starts with an ASCII `#UGC:2` header.
The last hexadecimal token on the first line is the section base.
The header ends at `#-END_OF_UGC_HEADER`.
A product banner follows, then a fixed-width `#UGC_TOC` table.

| Field | Meaning |
| --- | --- |
| `#UGC:2 PART` | Part document |
| `#UGC:2 ASSEMBLY` | Assembly document |
| `#- CMNM` | Common model name |
| `#UGC_TOC` | Section directory |
| `NEXT_TOC_ENTRY` | Continuation table |
| `1f 9d` | Unix-compress section payload |

Section offsets are relative to the header base.
Stored lengths include the `#<name>\n` section header.
The reader validates each extent before exposing a section.

## Reading

The reader returns a `CadDocument` with:

- source identity, PSB container version, and product version;
- model kind, common name, header lines, and section inventory;
- the native JPEG thumbnail as an auxiliary payload;
- the retained source bytes and digest;
- a warning that native geometry and feature records remain encoded.

The reader does not report bodies, sketches, dimensions, or a feature timeline.
Do not treat a successful read as native geometry coverage.

## Writing

The writer supports exact source replay only.
It requires the retained source bytes and verifies their digest before writing.
It refuses a document without retained Creo source bytes.

The result reports `mode="exact_native_roundtrip"`.
It keeps `vendor_loadable` and `application_usable` false because this path does not measure a newly authored model.

## Limits

- No independent PSB writer.
- No native feature or B-rep decoding.
- No assembly component resolution.
- No drawing, format, section, or layout support.
- No claim of lossless cross-format translation.

## Sources

- [Adapter](../../../src/convert/adapters/creo/Adapter.py)
- [Header](../../../src/convert/adapters/creo/Header.py)
- [Table of contents](../../../src/convert/adapters/creo/Toc.py)
- [Reader](../../../src/convert/adapters/creo/Reader.py)
- [Writer](../../../src/convert/adapters/creo/Writer.py)
- [Container findings](../../../re/creo/container/Container.md)
- [Writer gap](../../../re/creo/open-items/WriterGap.md)
- [ARM64 startup gotcha](../../Gotchas/Conversion/CreoArm64Startup.md)
- [Legacy ASCII rejection gotcha](../../Gotchas/Conversion/CreoLegacyAsciiRejected.md)
- [Change entry](../../Changes/Creo/CreoPsbContainer.md)
