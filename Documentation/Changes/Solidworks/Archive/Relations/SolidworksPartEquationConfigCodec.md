# Typed SOLIDWORKS part equation configuration codec

The internal version-19000 Config-0 serializer can read and re-emit an ordinary part equation graph when the caller sets `PartRelations=True` on both archive operations. It preserves the two equation sides, their parsed elements and back-references, and the real feature and sketch dimension handles. The default configuration profile rejects unclassified populated relations.

Both disclosed native saves return all 65,148 Config-0 bytes and the original object map. The pristine empty-manager control is byte-identical under either profile. Two independent source replays and seven configuration and construction regression cases pass. General equation classes, fresh neutral construction and public conversion remain open. [Replay receipt](../../../../../re/solidworks/measurements/2026/PartEquationConfigReplay01.json)

[Native field ownership and reproduction](../../../../../re/solidworks/records/PartEquationConfig2026.md) and [token range gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Equations/EquationSidesOwnLocalTokenRanges.md)
