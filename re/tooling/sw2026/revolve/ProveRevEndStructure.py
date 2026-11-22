from argparse import ArgumentParser
from codecs import lookup
from importlib import import_module
from io import BytesIO
from json import dumps
from math import cos, dist, isclose, sin
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE.parent))

from ProveMeasuredPrincipalRevolve import WriterAudit, digest
from convert import open_document, write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Revolves.Part.EmitRevStreams import EmitRevStreams
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Core.Preparation.Revolve.PrepareRevolve import PrepareRevolve
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Selection import Selection, SelectPathElem
from interchange.geometry.Models.Sketch import ConstraintRef, Sketch, SketchEntity, SketchRelation
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector

FORMAT = "solidworks.sldprt"
CASES = {
    "EndMidplane": ("Right", "symmetric_full", False, -7.25, (8.5, 22.75), (-5.5, 19.25), (2.125,)),
    "EndTwo": ("Top", "two_sided", False, 3.75, (11.5, 26.75), (-13.5, 4.0), (2.375, 0.5625)),
    "EndTwoReverse": ("Right", "two_sided", True, 8.25, (10.25, 35.0), (6.75, 23.5), (1.125, 1.8125)),
}
FRAMES = {
    "Top": ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)),
    "Right": ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)),
}


def world(u, v, x, y):
    return tuple(a * x + b * y for a, b in zip(u, v, strict=True))


def cross(a, b):
    x, y, z = a
    u, v, w = b
    return y * w - z * v, z * u - x * w, x * v - y * u


def source_model(case):
    plane, mode, reverse, offset, (inside, outside), (low, high), angles = case
    u, v, normal = FRAMES[plane]
    axis = tuple(-value if reverse else value for value in v)
    corners = (PlaneVector(offset + inside, low), PlaneVector(offset + outside, low),
               PlaneVector(offset + outside, high), PlaneVector(offset + inside, high))
    edge_ids = tuple(f"edge/{index}" for index in range(4))
    edges = tuple(SketchEntity(edge_id, GeometryKind.KLine, LineGeometry(corners[i], corners[(i + 1) % 4]))
                  for i, edge_id in enumerate(edge_ids))
    relations = tuple(SketchRelation(f"relation/{i}", "horizontal" if i % 2 == 0 else "vertical", (ConstraintRef(edge_id),))
                      for i, edge_id in enumerate(edge_ids))
    axis_start = low - 4.5
    axis_end = high + 6.0
    axis_entity = SketchEntity("axis", GeometryKind.KLine, LineGeometry(
        PlaneVector(offset, axis_start), PlaneVector(offset, axis_end)), construction=True)
    support = SupportPlane("plane", plane + " Plane", Transform(
        SpaceVector(0.0, 0.0, 0.0), SpaceVector(*u), SpaceVector(*v), SpaceVector(*normal)))
    sketch = Sketch("sketch", "IndependentMeridian", support.id, (*edges, axis_entity), relations,
                    closed_profile_entity_ids=(edge_ids,))
    selection = Selection("select/axis", "Axis", (
        SelectPathElem("sketch", sketch.id),
        SelectPathElem("sketch_entity", axis_entity.id),
    ))
    drivers = tuple(Parameter(f"angle/{index}", f"D{index}", ParameterValue(angle, ValueKind.KAngle, "rad"),
                              owner_id="feature") for index, angle in enumerate(angles, 1))
    definition = AngularRevolve(
        selection.id, drivers[0].id, SpaceVector(*world(u, v, offset, axis_start)), SpaceVector(*axis), mode,
        against_parameter_id=drivers[1].id if len(drivers) == 2 else None)
    feature = FeatureStep("feature", "IndependentBoss", FeatureKind.KRevolution, 0, sketch_id=sketch.id,
                          parameter_ids=tuple(driver.id for driver in drivers), operation=BooleanOp.KCreate,
                          definition=definition, selection_ids=(selection.id,))
    name = "Structural" + plane + ("Reverse" if reverse else mode.title().replace("_", ""))
    document = CadDocument(CadSource("kit-neutral", "<independent-authored>", "0" * 64),
                           (Configuration("configuration", "Default", True),), drivers, (support,), (sketch,),
                           (selection,), (feature,), (DesignBody("body", feature.name, feature.id),),
                           metadata={"name": name})
    return document


def expect_shape(document, case, include_brep):
    plane, mode, reverse, offset, (inside, outside), (low, high), angles = case
    (feature,) = (row for row in document.feature_timeline if type(row.definition) is AngularRevolve)
    (body,) = document.bodies
    (sketch,) = document.sketches
    (selection,) = document.selections
    (support,) = (row for row in document.support_planes if row.id == sketch.support_plane_id)
    drivers = [next(row for row in document.parameters if row.id == key) for key in feature.parameter_ids]
    ids = [row.id for row in drivers]
    u, v, _ = FRAMES[plane]
    axis = tuple(-number if reverse else number for number in v)
    start, end = (-angles[0] / 2, angles[0] / 2) if len(angles) == 1 else (-angles[1], angles[0])
    assert feature.definition.SideMode == mode and feature.attributes["native_reverse_direction"] is reverse
    assert tuple(driver.value.value for driver in drivers) == angles
    assert [row.name for row in drivers] == ["D1", "D2"][:len(angles)]
    assert all(row.owner_id == feature.id and row.role == "driving" and row.value.unit == "rad" for row in drivers)
    assert feature.definition.AlongParameterId == ids[0]
    assert feature.definition.AgainstParameterId == (ids[1] if len(ids) == 2 else None)
    assert tuple((feature.definition.AxisDirection.x, feature.definition.AxisDirection.y, feature.definition.AxisDirection.z)) == axis
    assert support.name == plane + " Plane" and feature.sketch_id == sketch.id
    assert feature.definition.AxisSelectionId == selection.id and selection.path[0].entity_id == sketch.id
    assert selection.path[-1].entity_id == next(row.id for row in sketch.entities if row.construction)
    assert body.final_feature_id == feature.id and len(sketch.constraints) == 4
    topology = body.topology
    assert (topology.solid_count, topology.face_count, topology.edge_count, topology.vertex_count) == (1, 6, 12, 8)
    span, height = end - start, high - low
    ring = outside**2 - inside**2
    volume = 0.5 * ring * height * span
    area = (height * (inside + outside) + ring) * span + 2 * height * (outside - inside)
    assert isclose(topology.volume, volume, rel_tol=1e-12)
    assert isclose(topology.surface_area, area, rel_tol=1e-12)
    assert (document.brep is not None) == include_brep
    if include_brep:
        assert not document.brep.validate(frozenset((body.id,)))
        vertices = [(row.point.x, row.point.y, row.point.z) for row in document.brep.vertices]
        for phi in (start, end):
            radial = world(u, cross(axis, u), cos(phi), sin(phi))
            for axial in (low, high):
                center = world(u, v, offset, axial)
                for radius in (inside, outside):
                    point = tuple(a + radius * b for a, b in zip(center, radial, strict=True))
                    assert sum(dist(point, item) <= 1e-10 for item in vertices) == 1, (point, vertices)
    return {"mode": mode, "reverse": reverse, "plane": plane, "target_angles": angles,
            "angle_span": [start, end], "volume_mm3": volume, "area_mm2": area,
            "signed_cap_corners_checked": include_brep}


def altered_end(part, field, value):
    fields = part.EndValue.FieldsValue
    old = fields[field]
    fields[field] = value
    try:
        streams, _, _ = EmitRevStreams(part.SystemValue, part.ResolvedValue.RootsValue, part.HeadersValue,
                                       part.DefinitionValue, part.InputValue, part.PlanValue)
        return BuildSldprt(streams, FormatVersion=4)
    finally:
        fields[field] = old


def invalid_dimension(part):
    first = part.EndValue.FieldsValue["f18"].FieldsValue["f850"][0]["o"].FieldsValue["ff0"].FieldsValue
    second = part.EndValue.FieldsValue["f20"].FieldsValue["f850"][0]["o"].FieldsValue["ff0"].FieldsValue
    assert first is not second
    saved = second["f50"]
    second["f50"] = first["f50"]
    try:
        streams, _, _ = EmitRevStreams(part.SystemValue, part.ResolvedValue.RootsValue, part.HeadersValue,
                                       part.DefinitionValue, part.InputValue, part.PlanValue)
        return BuildSldprt(streams, FormatVersion=4)
    finally:
        second["f50"] = saved


def reject_read(raw, problem, geometry):
    try:
        open_document(BytesIO(raw), source_format=FORMAT, strict=True, include_brep=geometry)
    except ValueError as error:
        assert "cache-free revolve has unverified typed history" in str(error)
        assert problem in str(error.__cause__), (problem, error.__cause__)
        return
    raise AssertionError("foreign end ownership opened successfully")


def verify(case_name, scratch):
    case = CASES[case_name]
    document = source_model(case)
    for module in ("interchange.brep.Validation.BrepValidate", "interchange.document.Models.DocumentProvenance"):
        import_module(module)
    lookup("utf-16-le")
    document.assert_valid()
    options = WriteOptions(values={"final_destination": rf"C:\KitStructuralRev\{document.metadata['name']}.SLDPRT"})
    audit = WriterAudit(scratch)

    def exercise():
        part = PrepareRevolve(document, BytesIO(), 1789123456, options)
        payload = part.BytesValue
        results = [
            expect_shape(open_document(BytesIO(payload), source_format=FORMAT, strict=True, include_brep=geometry), case, geometry)
            for geometry in (True, False)
        ]
        assert all(result["target_angles"] == case[-1] for result in results)
        two_sided = case[1] == "two_sided"
        broken = [("aliased_display" if two_sided else "unexpected_secondary",
                   altered_end(part, "f20", part.EndValue.FieldsValue["f18"]),
                   "distinct D1 and D2 owners" if two_sided else "end words and secondary owner disagree")]
        if two_sided:
            broken.append(("duplicate_dimension_identity", invalid_dimension(part), "distinct D1 and D2 owners"))
        for _, raw, error in broken:
            for geometry in (True, False):
                reject_read(raw, error, geometry)
        for send in (lambda sink: SldprtWriter().write(document, sink, options),
                     lambda sink: write_document(document, sink, destination_format=FORMAT,
                                                 values=options.values, allow_carrier=False)):
            sink = BytesIO(b"previous")
            try:
                send(sink)
            except ValueError as error:
                assert "requires an offline native measurement receipt" in str(error)
            else:
                raise AssertionError("unmeasured structural file was published")
            assert sink.tell() == 0 and sink.getvalue() == b"previous"
        return {"case": case_name, "archive_sha256": digest(payload), "views": results,
                "owner_refusals": [name for name, _, _ in broken], "public_receipt_refusals": 2}

    return audit.run(exercise) | {"audit": audit.report(), "native_launches": 0}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--case", choices=tuple(CASES), required=True)
    args = parser.parse_args()
    with TemporaryDirectory(prefix="KitRevEndStructure-") as directory:
        print(dumps(verify(args.case, Path(directory).resolve()), sort_keys=True))
