# Circular rim radius is owned by edge data

Expected: a fillet feature's direct radius reference identifies its driving radius.

Observed: the measured circular rim feature has null `rParamRadius`. Its single `DcFilletEdgeData.radiusValue` owns a reciprocal `DcDoubleParameter`/`Parameter` pair. A second owned pair carries dimensionless literal TangencyWeight one. Healthy parameter updates report false body/predecessor flags while feature/reference updates report true.

Follow actual role and reciprocal owner links, preserve both IDs and expressions, validate update state by role and refuse unsupported modes. Do not substitute an absent feature reference, invent a radius or apply length units to weight.

[Frozen source policy](../../../../../re/Fusion/DecodedPromotion20261127/RimFilletPolicy/Rules.md) · [Reader](../../../../Changes/Fusion/Readers/FusionCircularRimReader.md)
