# Thin extrusion native and API operation codes

A Fusion thin extrusion's saved `booleanOperation` and the vendor API's `operation` property use different integer enumerations. The saved cut code is 2 and the API cut code is 1. Decode the saved value through the native extrusion vocabulary and compare the resulting operation name against the enum recorded by the vendor study. Local file-driven runs verified cut, join and intersect independently.

[Vendor observations](../../../../re/Fusion/Study/thinextrudeoperations-edb76642a509/ground_truth.json) · [Native extrusion vocabulary](../../../../src/convert/Formats/Fusion/DocumentCodec/PartFeatures/Extrude/ExtrudeShape.py)
