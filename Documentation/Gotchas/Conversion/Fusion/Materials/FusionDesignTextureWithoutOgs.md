# Fusion Design texture mapping can exist without graphics

The saved body's `textureMapping` can resolve to a Layered mapping and its ASM and procedural layers even when the document contains no OGS graphics scene. Prepared material requests once checked the presence of graphics and missed this separate Design state.

The strict Fusion reader retains the mapping in public version-2 JSON. The [authored material procedure](../../../../Changes/Research/Encoder/FusionAuthoredMaterialProperties.md) refuses the mapping before preparing a request. Recovering a writable placement requires independent typed layer and cache rules.
