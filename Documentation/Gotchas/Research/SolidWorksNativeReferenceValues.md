# SOLIDWORKS native origin and empty direction values

## Expectation

The built-in origin reference always reports sketch-point type 8. An extrusion with no authored direction reference returns zero references.

## Actual behavior

SOLIDWORKS 34.4.1 reported point type 1 and zero coordinates for the point owned by the P03 `OriginProfileFeature`. Dynamic and generated interface calls agreed. The [point-type enumeration](https://help.solidworks.com/2025/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swSketchPointType_e.html) defines 1 as `User` and 8 as `Origin`.

For the ordinary P03 extrusion, `GetDirectionReference` returned -1, two null objects, and two type outputs of -1. The [method reference](https://help.solidworks.com/2022/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IExtrudeFeatureData2~GetDirectionReference.html) describes the positive reference counts but does not describe this complete empty tuple.

## Workaround

Establish the origin through its unique built-in sketch owner and zero coordinates, then accept the observed point types 1 and 8. For a default extrusion direction, require an empty result across all five outputs. A positive count, non-null reference, or populated type remains unsupported by this collector.

These rules correct oracle collection. They do not establish full source-decoder acceptance. See [the change entry](../../Changes/Research/Verification/NativeReferenceContracts.md).
