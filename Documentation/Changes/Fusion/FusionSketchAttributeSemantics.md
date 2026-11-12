# Typed ASCII sketch attributes

## Behavior

The BRep `SketchLink` model now uses the native field meanings: `PrimaryId`, `SecondaryId`, `Direction`, `SplitSequenceId`, `SplitTotalNumber`, and `TopologyRoleFlags`. The first five positional arguments retain their order; the explicit role-flags argument defaults to zero.

Both curve identities are unsigned 64-bit integers. The split fields are unsigned 32-bit values satisfying `1 <= sequence <= total`. The qualified direction domain is `0`, `1`, and `UINT32_MAX`, where the last value is a native comparison wildcard. The current profile still rejects nonzero topology role flags.

The ASCII attribute stores the fields in this order:

```text
primary secondary direction topologyRoleFlags splitSequenceId splitTotalNumber
```

The fourth word is persisted state, not an inserted separator. The final words describe a fragment ordinal and total, not unrelated enumerations. The [field-order gotcha](../../Gotchas/Conversion/Fusion/FusionSketchAttributeOrder.md) contrasts this form with the binary Design callback.

## Direction reversal

The derived selection snapshot reverses concrete directions with `1 - direction` and retains `UINT32_MAX` as a wildcard. This is a semantic inference from the native comparison rule, which accepts either wildcard regardless of the other direction. No named native flip implementation was identified. The existing zero/one authoring defaults keep identical serialized bytes.

## Evidence and verification

[Native stream operators and read-only corpus evidence](../../../re/Fusion/Reconstruction/EntityGraph/SketchAsciiSemantics.md) identify every field's offset and unsigned integer width. All 1,083 distinct ASM blobs yielded 20,636 ASCII sketch attributes, including archived revisions. They contain 350 nonzero secondary identities, 99 wildcard directions, and 456 nontrivial split pairs; every observed role-flags word is zero.

New archive compatibility cases carry unsigned identities, wildcard directions, and split pairs through complete history/snapshot serialization and reading. Three malformed split-pair cases require rejection after ZIP loading. These run remotely only. Black, Ruff, Mypy, Pyright, and steering compliance passed for the seven directly changed Python files.

The broader generic-tag correction and existing authoring fixture comparison are documented in [FusionGenericTagSemantics.md](FusionGenericTagSemantics.md). This field-domain qualification does not make arbitrary identifiers valid references to a particular Design sketch.
