# Ordinary downstream archive grammar

The research ledger now records the exact-build ordinary version-19000 direct body of `moDownstreamIdData_c`: seven u32 words, the four-byte `su_CTime` encoding, eighteen fixed-i32-counted collections, typed pointer constraints, UUID/key framing and the twenty-byte `uniqueIdInfo_c` body. It separates the ordinary per-configuration stream from Config condition `0x80` and preserves native load normalization as a distinct operation.

Use the [field-order record](../../../../../re/solidworks/records/DownstreamIdArchiveGrammar2026.md) and its numeric JSON when implementing or reviewing a future codec. The [conditional-object gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Downstream/DownstreamMapsHaveConditionalObjects.md) explains the five key/value maps. This adds format knowledge only; no SDK profile, reader, writer, allocator, default or public capability changes.

Verification inspected the pinned original 2026 modules and bound 31 complete native owners/leaves, 32 instruction windows, eight descriptors/virtual cells and 31 selected imports. No schema, codec, tests, VM or CAD application ran. No matching saved downstream stream was read. Actual archive-map initialization, reached polymorphic closure, full replay and controlled native acceptance remain required. No native or held-out acceptance is claimed.
