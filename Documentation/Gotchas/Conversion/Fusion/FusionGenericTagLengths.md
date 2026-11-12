# Generic-tag counts are primary byte lengths

## Expectation

Small leading integers in generic-tag groups can appear to identify body, face, or edge categories.
The next integer after primary text can appear related to history generation.

## Actual behavior

Native `tag_data::save` derives the leading integer from its primary byte-array length.
Native accessors identify the subsequent fields as secondary identity, operation identities, and approach identity.

The earlier body writer emitted a fixed count of three.
That matches primary text `301` but disagrees with four-digit primary text such as `1701`.
Earlier feature callers supplied matching counts for their short labels, which concealed the mistaken selector interpretation.

The native cuboid body has secondary identity seven and primary text `301`.
That secondary identity matches its body progenitor tag, rather than naming the current history state.
The controlled cylinder uses secondary identity four.

## Workaround

Construct semantic `FeatureTag` values without a supplied length.
Derive the encoded count from the primary bytes and reject inconsistent counts when reading.
Use `BodyIdentity.SecondaryId` for the explicit secondary identity.
Keep history generation in `HistoryState`, where it has its own independent field.

The qualified primary-text domain is printable ASCII, with one through 255 bytes.
Signed 32-bit native tag identities remain signed even when the stream uses 64-bit integer tokens.

## Evidence

The [native instruction report](../../../../re/Fusion/Reconstruction/CuboidHistory/GenericTagEvidence.json)
records the serializer chain and 441 consistent groups from the research corpus.
The [semantic correction](../../../Changes/Fusion/FusionGenericTagSemantics.md)
describes API migration and archive integration coverage.

Previously accepted three-digit authoring defaults retain their serialized bytes.
The correction does not retrospectively establish native acceptance for earlier malformed four-digit output.
