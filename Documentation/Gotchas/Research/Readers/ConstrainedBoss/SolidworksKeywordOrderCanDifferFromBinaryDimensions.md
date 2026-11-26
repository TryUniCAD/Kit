# SOLIDWORKS keyword order can differ from binary dimensions

In the pinned P03 source and original generated part, the binary sketch stores width then height with the same directed point IDs. The source keyword index lists height then width, while the original generated keyword index lists width then height. The scoped SDK fallback binds binary rows by name but keeps the keyword order in its projected constraint tuple.

Inspect both streams when a projected order differs. The P03 opt-in writer uses the proved source relation identities to choose the keyword order before encoding. The exact comparison changed that one clear stream and retained every binary dimension and PMI byte in the generated part. [P03 replay and verification](../../../../Changes/Research/Encoder/SolidworksKeywordDimensionOrder.md)
