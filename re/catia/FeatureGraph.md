# CATIA OSMX feature graph

## What is decoded

The outer `CATPrtCont` and `CATProdCont` streams start with `OSMX`. The OSMX stream has a symbol
table at offset 100, a `|\x02` marker, a section length, and a symbol data section. The symbol table
contains class names, plane names, and part names.

The reader exposes the symbol table as `catia.native_symbols`, `catia.part_symbols`, and
`catia.product_symbols`. It also exposes the three principal planes as `SupportPlane` records.

## What is not decoded

The OSMX stream is a symbol table, not the complete feature graph. The feature records, sketch
records, dimensions, constraints, and relations are not decoded. The reader retains the exact OSMX
bytes as a `NativeFeatureDefinition` payload.

## Evidence

- `src/convert/adapters/catia/Container.py` parses the OSMX symbol table.
- `src/convert/adapters/catia/Adapter.py` exposes the symbol table and principal planes.
- `CATObjectModelerBase.dll` SHA-256 `a522a0a040c74fc8f53aea707785e0d00e836d9eb8a113a25349fbd985905980`.
- `CATOmbPrivateSavePersistServices::StreamDocumentToPath` at `0x180119290`.
- `CATOmbPrivateLoadPersistServices::UnstreamDocument` at `0x180115620`.

## Open work

1. Locate the feature-record stream and its class table.
2. Decode sketch entities and constraints.
3. Decode dimensions and relations.
4. Emit a live feature tree and measure a dimension edit in CATIA.
