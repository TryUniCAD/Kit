# Editable FreeCAD primitives can have opaque neutral definitions

The strict SDK reads both tracked historical AdditiveBox controls as `primitive` plus `NativeFeatureDefinition`. Each archive has a real `PartDesign::AdditiveBox`, stored drivers and a linked `PartDesign::Body` with its own Shape. Both strict reads also include an analytic rectangular B-rep.

Check the physical source class and owned dependency graph before choosing an imported-body route. The opaque definition marks a typed decoding boundary. The saved solid alone leaves the primitive's editable intent unresolved. [Pinned source census](../../../../re/solidworks/records/BakedFcstdSourceEligibility2026.md) · [FreeCAD feature decoder](../../../../src/convert/adapters/freecad/Native.py)
