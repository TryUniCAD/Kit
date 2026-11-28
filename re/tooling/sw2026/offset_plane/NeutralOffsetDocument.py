from hashlib import sha256
import json


def make_document(case):
    from interchange.document.Models.DocumentModel import CadDocument
    from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
    from interchange.Enums.EnumGeometry import GeometryKind
    from interchange.Enums.EnumValues import ValueKind
    from interchange.Features.FeatureBody import DesignBody
    from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
    from interchange.Features.FeatureKinds import RefPlaneFeature
    from interchange.Features.FeatureStep import FeatureStep
    from interchange.geometry.Models.GeometryCurves import CircleGeometry
    from interchange.geometry.Models.Sketch import (
        ConstraintRef,
        Sketch,
        SketchEntity,
        SketchRelation,
    )
    from interchange.geometry.Models.SupportPlane import SupportPlane
    from interchange.geometry.Models.Transform import Transform
    from interchange.geometry.Models.VectorPlane import PlaneVector
    from interchange.geometry.Models.VectorSpace import SpaceVector
    from interchange.Records.RecordConfig import Configuration
    from interchange.Records.RecordParameter import Parameter, ParameterValue
    from interchange.Records.RecordSource import CadSource

    def length(value, unit="mm"):
        return ParameterValue(value, ValueKind.KLength, unit)

    axes = {
        "front": ("Front Plane", (1, 0, 0), (0, 1, 0), (0, 0, 1)),
        "top": ("Top Plane", (1, 0, 0), (0, 0, -1), (0, 1, 0)),
        "right": ("Right Plane", (0, 0, -1), (0, 1, 0), (1, 0, 0)),
    }
    name, tangent, transversal, normal = axes[case["base"]]
    signed = case["distance_m"] * (-1 if case["reverse"] else 1)
    signed_mm = signed / 0.001
    offset_unit = case.get("offset_unit", "mm")
    offset_value = signed if offset_unit == "m" else signed_mm
    radius, depth = case["radius_m"] / 0.001, case["depth_m"] / 0.001
    basis = (SpaceVector(*tangent), SpaceVector(*transversal), SpaceVector(*normal))
    plane = SupportPlane(
        "base", case.get("plane_name", name),
        Transform(SpaceVector(0.0, 0.0, 0.0), *basis),
    )
    carrier = SupportPlane(
        "carrier",
        case.get("datum_name", "OffsetPlane"),
        Transform(SpaceVector(*(signed_mm * value for value in normal)), *basis),
        offset_parameter_id="offset-distance",
    )
    offset = FeatureStep(
        "datum",
        carrier.name,
        FeatureKind.KReference,
        0,
        parameter_ids=("offset-distance",),
        definition=RefPlaneFeature(carrier.id, plane.id, length(offset_value, offset_unit)),
    )
    entity = SketchEntity(
        "circle", GeometryKind.KCircle, CircleGeometry(PlaneVector(0.0, 0.0), radius)
    )
    sketch = Sketch(
        "sketch",
        case.get("sketch_name", "PlaneSketch"),
        carrier.id,
        (entity,),
        (
            SketchRelation(
                "radius-constraint",
                "radius",
                (ConstraintRef(entity.id),),
                "radial-length",
            ),
            SketchRelation(
                "centre-fix", "fixed", (ConstraintRef(entity.id, "center"),)
            ),
        ),
        ("radial-length",),
        ((entity.id,),),
    )
    boss = FeatureStep(
        "boss",
        case.get("boss_name", "PlaneBoss"),
        FeatureKind.KExtrusion,
        1,
        input_feature_ids=(offset.id,),
        sketch_id=sketch.id,
        parameter_ids=("depth-length",),
        operation=BooleanOp.KCreate,
        definition=ExtrudeFeature(length(depth), ExtrudeEnd.KBlind),
    )
    signature = sha256(
        json.dumps(case, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()
    document = CadDocument(
        source=CadSource("kit.neutral", "<authored design>", signature),
        configurations=(Configuration("default", case.get("configuration_name", "Default"), True),),
        parameters=(
            Parameter("offset-distance", "D1", length(abs(offset_value), offset_unit), owner_id=offset.id),
            Parameter("radial-length", "D1", length(radius), owner_id=sketch.id),
            Parameter("depth-length", "D1", length(depth), owner_id=boss.id),
        ),
        support_planes=(plane, carrier),
        selections=(),
        sketches=(sketch,),
        feature_timeline=(offset, boss),
        bodies=(DesignBody("body", boss.name, boss.id),),
        metadata={"name": case["name"]},
        units="mm",
    )
    document.assert_valid()
    return document
