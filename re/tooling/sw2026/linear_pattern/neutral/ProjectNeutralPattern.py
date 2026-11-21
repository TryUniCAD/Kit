from dataclasses import asdict
from math import dist, pi
from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadBossEnd import ReadBossEnd
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadCircParams import CheckCircDrive
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import ReadLength
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import ReadPrincAxis
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequireExtrusion import RequireExtrude
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import ReadStyleText
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ReadStockRectangle import ReadStockRect
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentValidate import AssertValid
from interchange.Enums.EnumDocument import Capability
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.BoundPlaneValues import ReadPlaneParam
from interchange.Features.FeatureBoundPlane import BoundDatum
from interchange.Features.FeatureExtrude import ExtrudeEnd
from interchange.Features.FeatureKinds import LinearPattern
from interchange.Features.PlaneExtAxis import GetExtVector
from interchange.geometry.Models.Selection import SelectPathElem
from interchange.Records.RecordTopology import TopologyCounts

from CheckPatternAngleOwners import require
from MakeLocalPattern import LocalPatternIntent
from MakeLocalPatternDrivers import check_styles
from MakePatternAngularPlane import AngularPlaneIntent
from MakePatternAnnotationCatalog import annotation_frame
from MakePatternSeed import FrontBlindIntent, RaisedSeedIntent
from NeutralPatternInput import (AngularLabelIntent, AnnotationViewIntent, NeutralPatternInput,
                                 PatternPresentation, PlaneIntersectionAxis)
from PatternBoxGeometry import contained_boxes
from PatternHingeGeometry import ORIGIN, derive_hinge


SYSTEM_PLANES = ("Front Plane", "Top Plane", "Right Plane")
NEUTRAL_CAPS = frozenset({
    Capability.KParameters, Capability.KParamHistory, Capability.KSupportPlanes,
    Capability.KEditableSketches, Capability.KSelections, Capability.KBodyStructure,
    Capability.KConfigurations,
})


def expect_plain(record):
    return not record.attributes and record.provenance is None


def map_by_id(records):
    values = {record.id: record for record in records}
    require(len(values) == len(records) and all(type(key) is str and key.strip() for key in values),
            "neutral owner IDs are missing or ambiguous")
    return values


def compare_choice(selection, kind, target, subelement=""):
    require(selection.path == (SelectPathElem(kind, target, subelement),) and not selection.query
            and selection.point is None and expect_plain(selection),
            "neutral selection does not name its exact local " + (subelement or kind) + " owner")


def scoped_document(value):
    require(type(value) is CadDocument, "expected a real neutral CadDocument")
    require(value.units is UnitSystem.KMillimeter and value.schema_version == "1.0"
            and value.brep is value.assembly is value.DrawingValue is None
            and not (value.meshes or value.brep_payloads or value.diagnostics or value.materials or value.source.attributes)
            and not (value.capabilities - NEUTRAL_CAPS),
            "oblique research input needs an ordinary neutral part without additional geometry or semantics")
    require(set(value.metadata) == {"name"}, "only the ordinary neutral part name is admitted as metadata")
    require(len(value.configurations) == 1, "oblique research input needs one active ordinary configuration")
    config, = value.configurations
    require(config.active is True and config.parent_id is None and not
            (config.overrides or config.suppressed_feature_ids or config.attributes), "unsupported configuration state")
    require(len(value.feature_timeline) == 5 and len(value.parameters) == 6 and len(value.bodies) == 1
            and len(value.sketches) == 2 and len(value.support_planes) == 4 and len(value.selections) == 7,
            "oblique research input needs the complete owned five-operation document graph")
    require(all(expect_plain(step) and not step.suppressed and not step.configuration_states
                for step in value.feature_timeline), "neutral timeline contains extra feature state")
    require(all(left.order < right.order for left, right in zip(value.feature_timeline, value.feature_timeline[1:])),
            "neutral operation order must retain the two stocks followed by their datum and pattern")
    require(all(expect_plain(record) for record in (*value.parameters, *value.support_planes, *value.sketches,
                                                     *value.bodies, *(entity for sketch in value.sketches
                                                                      for entity in sketch.entities))),
            "unrepresented provenance or extension in neutral part")
    AssertValid(value)
    return config


def principal_planes(planes, support_id):
    principal = {plane.name: plane for plane in planes.values() if plane.id != support_id}
    require(set(principal) == set(SYSTEM_PLANES)
            and all(plane.support_selection_id is None and plane.offset_parameter_id is None
                    for plane in principal.values()), "expected exactly unbound canonical Front, Top and Right supports")
    require(all(ReadPrincAxis(principal[name].transform) == axis
                for name, axis in zip(SYSTEM_PLANES, ("z", "y", "x"), strict=True)),
            "fixed support name and actual frame disagree")
    return tuple(principal[name] for name in SYSTEM_PLANES)


def blind_stock(step, sketch, front, driver, previous=(), picks=()):
    definition = RequireExtrude(step, BooleanOp.KJoin if previous else BooleanOp.KCreate, previous,
                                ExpectedSelections=picks)
    CheckCircDrive(driver, step.id, "D1")
    require(type(step.parameter_ids) is tuple and step.parameter_ids == (driver.id,)
            and definition.length == driver.value and definition.end_condition is ExtrudeEnd.KBlind
            and definition.reversed is False and definition.symmetric is False
            and sketch.support_plane_id == front.id and not sketch.parameter_ids,
            "stock needs its actual Front rectangle and sole positive forward blind D1")
    vertices = ReadStockRect(sketch, 0.001)
    end = ReadBossEnd(definition, "z")
    return FrontBlindIntent(sketch.name, step.name, ((*vertices[0], 0.0), (*vertices[2], end.DepthValue)))


def check_axis(axis, plane, top, right, choices, plate, seed):
    definition = axis.definition
    require(type(definition) is PlaneIntersectionAxis and axis.kind is FeatureKind.KReference,
            "a typed finite plane-intersection axis is required")
    require(not (axis.parameter_ids or axis.input_feature_ids) and axis.operation is axis.sketch_id is None
            and axis.selection_ids == (definition.first_plane_selection_id, definition.second_plane_selection_id)
            and len(set(axis.selection_ids)) == 2, "finite axis must retain its two ordered support selections")
    first, second = (choices[key] for key in axis.selection_ids)
    compare_choice(first, "support_plane", top.id)
    compare_choice(second, "support_plane", right.id)
    finite = derive_hinge(plate.bounds_m, seed.bounds_m)
    endpoints = tuple(tuple(value * 1000.0 for value in point) for point in finite["ordered_endpoints_m"])
    require(all(dist(GetExtVector(point), expected) < 1e-10 for point, expected in
                zip((definition.start_mm, definition.end_mm), endpoints, strict=True)),
            "finite axis endpoints do not follow the directed first-plane trim")
    require(plane.ReferenceFrame == right.transform, "angled datum zero frame differs from its selected Right plane")


def datum_angle(step, axis, support, right, picks, parameters):
    definition = step.definition
    require(type(definition) is BoundDatum and definition.Method == "angle",
            "angled datum requires its actual bound angle and evaluated support")
    require(step.kind is FeatureKind.KReference and step.input_feature_ids == (axis.id,)
            and step.sketch_id is step.operation is None and len(step.selection_ids) == 2,
            "angled datum must depend on its preceding finite hinge and actual Right support")
    face, hinge = (picks[key] for key in step.selection_ids)
    compare_choice(face, "support_plane", right.id)
    compare_choice(hinge, "feature", axis.id)
    require(support.id == definition.SupportPlaneId and support.name == step.name
            and support.support_selection_id == face.id and support.offset_parameter_id == definition.OffsetParameterId,
            "angled datum output does not join its actual evaluated support")
    require(step.parameter_ids == (definition.ScalarParameterId, definition.OffsetParameterId)
            and len(set(step.parameter_ids)) == 2, "angled datum must retain actual scalar and zero-offset roles")
    angle, zero = (parameters[key] for key in step.parameter_ids)
    CheckCircDrive(angle, step.id, "D1")
    require(zero.owner_id == step.id and zero.name == "Reference offset"
            and zero.role is ParameterRole.KDerived and zero.expression is None
            and ReadPlaneParam(step, definition.OffsetParameterId, parameters, ValueKind.KLength) == 0.0,
            "inactive datum offset is only a derived zero invariant")
    value = ReadPlaneParam(step, definition.ScalarParameterId, parameters, ValueKind.KAngle)
    require(0.0 < value < pi / 2.0, "only the acute positive Right-plane angle profile is admitted")
    return angle.id, float(value)


def pattern_values(step, seed_step, angle_step, angled, choices, parameters):
    definition = step.definition
    require(type(definition) is LinearPattern and step.kind is FeatureKind.KPattern
            and step.operation is BooleanOp.KJoin and step.sketch_id is None
            and step.input_feature_ids == (seed_step.id, angle_step.id)
            and len(step.selection_ids) == 2 and step.selection_ids[0] == definition.direction_selection_id,
            "pattern must retain actual ordered seed and plane dependencies")
    direction, body = (choices[key] for key in step.selection_ids)
    compare_choice(direction, "support_plane", angled.id)
    compare_choice(body, "feature", seed_step.id, "body")
    require(len(step.parameter_ids) == 2, "pattern requires actual independent count and pitch drivers")
    count, pitch = (parameters[key] for key in step.parameter_ids)
    CheckCircDrive(count, step.id, "D1")
    CheckCircDrive(pitch, step.id, "D3")
    require(type(definition.reversed) is bool and type(definition.instance_count) is int
            and type(count.value.value) is int and count.value.kind == ValueKind.KInteger and count.value.unit == ""
            and count.value.value == definition.instance_count and pitch.value == definition.spacing,
            "pattern D1/D3 drivers disagree with the actual signed count and pitch")
    normal = GetExtVector(angled.transform.z_axis)
    return count, pitch, tuple(-value if definition.reversed else value for value in normal)


def presentation(value, angle_id, count_id, pitch_id):
    require(type(value) is PatternPresentation and type(value.angle) is AngularLabelIntent
            and (value.angle.parameter_id, value.count_parameter_id, value.pitch_parameter_id)
            == (angle_id, count_id, pitch_id), "presentation is not bound to the actual active parameter owners")
    require(type(value.views) is tuple and all(type(view) is AnnotationViewIntent for view in value.views)
            and type(value.shown) is tuple, "expected an explicit ordered typed annotation catalog")
    names = {view.name for view in value.views}
    require(len(names) == len(value.views) and value.angle.annotation_view == "*Back"
            and value.angle.annotation_view in names and {value.active, *value.shown} <= (names | {None}),
            "annotation view and active membership must bind the actual catalog")
    for view in value.views:
        annotation_frame(view.basis)
    check_styles(value.styles)
    return {"views": [asdict(view) for view in value.views], "active": value.active, "shown": value.shown}


def project(value):
    require(type(value) is NeutralPatternInput and type(value.output) is SelfFileInput,
            "expected a typed neutral part with explicit target identity")
    document = value.document
    config = scoped_document(document)
    name = ReadStyleText(document.metadata["name"], "neutral part name")
    path = PureWindowsPath(value.output.PathName)
    require(path.is_absolute() and str(path) == value.output.PathName and path.drive == "C:"
            and path.name == name + ".SLDPRT" and ".." not in path.parts
            and 0 < value.output.SavedAt < 0x7FFFFFFF, "target needs the exact authored native basename and event")
    plate, seed, hinge, angle, pattern = document.feature_timeline
    require(type(angle.definition) is BoundDatum, "angled datum requires an actual bound definition")
    planes, sketches, drivers, picks = map(map_by_id, (document.support_planes, document.sketches,
                                                       document.parameters, document.selections))
    angled = planes[angle.definition.SupportPlaneId]
    front, top, right = principal_planes(planes, angled.id)
    require(len(plate.parameter_ids) == len(seed.parameter_ids) == 1
            and len(seed.selection_ids) == 1 and {plate.sketch_id, seed.sketch_id} == set(sketches),
            "plate and seed must own exactly their own rectangle and depth driver")
    compare_choice(picks[seed.selection_ids[0]], "feature", plate.id, "body")
    require(len({identity for step in document.feature_timeline for identity in step.parameter_ids}) == len(drivers)
            and sum(len(step.parameter_ids) for step in document.feature_timeline) == len(drivers)
            and len({identity for step in document.feature_timeline for identity in step.selection_ids}) == len(picks)
            and sum(len(step.selection_ids) for step in document.feature_timeline) == len(picks),
            "neutral features must individually own every distinct parameter and selection")
    plate_box, seed_box = tuple(blind_stock(step, sketches[step.sketch_id], front, drivers[step.parameter_ids[0]],
                                           previous, step.selection_ids if previous else ())
                                for step, previous in ((plate, ()), (seed, (plate.id,))))
    check_axis(hinge, angle.definition, top, right, picks, plate_box, seed_box)
    angle_id, angle_rad = datum_angle(angle, hinge, angled, right, picks, drivers)
    count, pitch, direction = pattern_values(pattern, seed, angle, angled, picks, drivers)
    count_value, pitch_m = count.value.value, ReadLength(pitch.value)
    bodies = contained_boxes(plate_box.bounds_m, seed_box.bounds_m, direction, pitch_m, count_value)
    final, = document.bodies
    expected = TopologyCounts(solid_count=1, shell_count=1, face_count=6 + 5 * len(bodies),
                              edge_count=12 + 12 * len(bodies), vertex_count=8 + 8 * len(bodies))
    require(final.final_feature_id == pattern.id and final.name == pattern.name and final.material_id is None
            and final.topology in (TopologyCounts(), expected), "final neutral body contradicts the implicit joined result")
    shown = presentation(value.presentation, angle_id, count.id, pitch.id)
    label = value.presentation.angle
    seed_intent = RaisedSeedIntent(name, config.name, str(path), value.output.SavedAt, plate_box, seed_box)
    plane = AngularPlaneIntent(angle.name, angle_rad, False, label.annotation_view, label.design_intent,
                               label.selected_leader, label.shifted_point_m)
    pattern_intent = LocalPatternIntent(pattern.name, count_value, pitch_m, pattern.definition.reversed,
                                        value.presentation.styles)
    return seed_intent, hinge.name, plane, shown, pattern_intent
