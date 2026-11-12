# TSM link order and valence offsets

The first two fields of a TSM `l` record are previous then next. Reciprocal-ring validation alone cannot distinguish them because swapping both labels still produces reciprocal rings. Native `Link_prev` reads struct offset zero, and the serializer emits that offset first.

The final link word is not an uninterpreted flag field: its low two bits are native `Link_valenceOffset`. Face records similarly use bit zero of their second word for hidden state. Name these fields explicitly and reject unproved high bits. Validate opposite endpoints as well as reciprocal rings so the intended orientation is observable.

[Native getter and writer evidence](../../../../../re/Fusion/Reconstruction/TSpline/FieldEvidence.json) records the exact ARM64 offsets.
