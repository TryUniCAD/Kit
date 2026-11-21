from dataclasses import dataclass, replace
from math import isfinite

from convert.Geometry.Extrude.Polygon.PrismFrame import CheckPrismFrame
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadCircGeom import (
    ReadCircGeom,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadCircParams import (
    CheckCircDrive,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequireExtrusion import (
    RequireExtrude,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ReadStockRectangle import (
    ReadStockRect,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureExtrude import ExtrudeEnd
from interchange.geometry.Models.GeometryCurves import CircleGeometry, PointGeometry
from interchange.geometry.Models.Selection import SelectPathElem
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordTopology import TopologyCounts

LENGTH_UNITS = {"mm": 1.0, "m": 1000.0, "in": 25.4}


def require(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


def xyz(vector):
    return vector.x, vector.y, vector.z


def scaled(vector, factor):
    return SpaceVector(*(component * factor for component in xyz(vector)))


@dataclass(frozen=True)
class Stock:
    feature_id: str
    driver_id: str
    support_id: str
    frame: Transform
    corners: tuple[PlaneVector, PlaneVector, PlaneVector, PlaneVector]
    extent: tuple[float, float]


@dataclass(frozen=True)
class ShapeIntent:
    selected: Stock
    untouched: Stock
    cut_id: str
    selection_id: str
    circle: CircleGeometry
    cutter_direction: SpaceVector
    bodies: tuple[DesignBody, DesignBody]


def require_cold(document):
    require(
        isinstance(document, CadDocument), "cold shape requires a neutral CAD document"
    )
    require(
        document.brep is None and not document.brep_payloads and not document.meshes,
        "cold shape refuses cached geometry or native payloads",
    )
    require(
        document.assembly is None
        and document.DrawingValue is None
        and not document.materials
        and not document.source.attributes
        and not (set(document.metadata) - {"name"}),
        "cold shape requires ordinary neutral part intent",
    )
    require(
        tuple(
            map(
                len,
                (
                    document.configurations,
                    document.parameters,
                    document.support_planes,
                    document.sketches,
                    document.selections,
                    document.feature_timeline,
                    document.bodies,
                ),
            )
        )
        == (1, 2, 2, 3, 1, 3, 2),
        "cold shape needs exactly two stocks and one explicitly selected cut",
    )
    (config,) = document.configurations
    require(
        config.active
        and config.parent_id is None
        and not config.overrides
        and not config.suppressed_feature_ids
        and not config.attributes,
        "cold shape requires one unextended active configuration",
    )
    require(
        all(
            body.material_id is None
            and not body.attributes
            and body.topology == TopologyCounts()
            for body in document.bodies
        ),
        "cold shape refuses authored body extensions or saved summary geometry",
    )
    document.assert_valid()


def support_frame(plane, scale):
    require(
        plane.support_selection_id is None
        and plane.offset_parameter_id is None
        and not plane.attributes,
        "cold stock requires its direct fixed planar support",
    )
    frame = replace(plane.transform, origin=scaled(plane.transform.origin, scale))
    CheckPrismFrame(frame)
    require(
        all(
            sorted(abs(value) for value in xyz(axis)) == [0, 0, 1]
            for axis in (frame.x_axis, frame.y_axis, frame.z_axis)
        ),
        "cold stock support requires a signed cardinal basis",
    )
    return frame


def read_stock(feature, sketch, frame, params, scale):
    definition = RequireExtrude(feature)
    require(
        definition.end_condition == ExtrudeEnd.KBlind
        and definition.length is not None
        and not definition.symmetric
        and definition.second_length is None
        and definition.second_end_condition is None
        and type(definition.reversed) is bool
        and len(feature.parameter_ids) == 1
        and not sketch.parameter_ids,
        "cold stock needs its sole active blind length",
    )
    driver = params[feature.parameter_ids[0]]
    CheckCircDrive(driver, feature.id, "D1")
    length = driver.value
    require(
        length == definition.length
        and length.kind == ValueKind.KLength
        and length.unit in LENGTH_UNITS
        and type(length.value) in (int, float),
        "stock D1 disagrees with its live blind length",
    )
    depth = length.value * LENGTH_UNITS[length.unit]
    require(
        isfinite(depth) and depth > 0.0, "stock D1 must be finite and strictly positive"
    )
    effective = scaled(frame.z_axis, -1 if definition.reversed else 1)
    require(
        definition.direction in (None, effective),
        "stock direction contradicts its signed blind depth",
    )
    extent = (-depth, 0.0) if definition.reversed else (0.0, depth)
    corners = tuple(PlaneVector(*point) for point in ReadStockRect(sketch, scale))
    return Stock(feature.id, driver.id, sketch.support_plane_id, frame, corners, extent)


def read_circle(sketch, scale):
    require(
        not sketch.parameter_ids and not sketch.constraints,
        "through profile requires one free circle",
    )
    circles = tuple(
        entity for entity in sketch.entities if entity.kind == GeometryKind.KCircle
    )
    require(
        len(circles) == 1 and type(circles[0].geometry) is CircleGeometry,
        "through profile requires its sole analytic circle",
    )
    circle = circles[0]
    extra = tuple(entity for entity in sketch.entities if entity is not circle)
    if extra:
        require(
            len(extra) == 1
            and extra[0].kind == GeometryKind.KPoint
            and type(extra[0].geometry) is PointGeometry
            and extra[0].geometry.point == circle.geometry.center
            and not extra[0].construction
            and not extra[0].fixed
            and not extra[0].attributes,
            "through profile has alternate centre geometry",
        )
    value = ReadCircGeom(replace(sketch, entities=(circle,)), scale)
    return CircleGeometry(PlaneVector(*value.CenterValue), value.RadiusValue)


def project_intent(document):
    require_cold(document)
    require(
        document.units in LENGTH_UNITS,
        "cold shape requires an explicit supported length unit",
    )
    scale = LENGTH_UNITS[document.units]
    supports = {
        plane.id: support_frame(plane, scale) for plane in document.support_planes
    }
    sketches = {sketch.id: sketch for sketch in document.sketches}
    params = {value.id: value for value in document.parameters}
    first, second, cut = document.feature_timeline
    require(
        first.order < second.order < cut.order
        and {first.sketch_id, second.sketch_id, cut.sketch_id} == set(sketches),
        "cold operations must retain their three ordered profile owners",
    )
    require(
        set(supports)
        == {
            sketches[first.sketch_id].support_plane_id,
            sketches[second.sketch_id].support_plane_id,
        },
        "cold stocks must own two different supports",
    )
    stocks = tuple(
        read_stock(feature, sketch, supports[sketch.support_plane_id], params, scale)
        for feature in (first, second)
        for sketch in (sketches[feature.sketch_id],)
    )
    require(
        {stock.driver_id for stock in stocks} == set(params),
        "independent stocks need distinct D1 owners",
    )
    require(
        {tuple(abs(value) for value in xyz(stock.frame.z_axis)) for stock in stocks}
        == {(0, 0, 1), (1, 0, 0)},
        "cold stocks require signed Front and Right normals",
    )
    (choice,) = document.selections
    require(
        not choice.query
        and choice.point is None
        and not choice.attributes
        and len(choice.path) == 1,
        "cut requires one explicit historical body selection",
    )
    candidates = tuple(
        stock
        for stock in stocks
        if choice.path == (SelectPathElem("feature", stock.feature_id, "body"),)
    )
    require(
        len(candidates) == 1, "cut selection does not resolve to one actual prior stock"
    )
    (selected,) = candidates
    (untouched,) = (stock for stock in stocks if stock is not selected)
    definition = RequireExtrude(
        cut,
        BooleanOp.KCutOperation,
        (selected.feature_id,),
        ExpectedSelections=(choice.id,),
    )
    sketch = sketches[cut.sketch_id]
    require(
        sketch.support_plane_id == selected.support_id,
        "through cut must use its selected stock's actual support",
    )
    require(
        definition.end_condition == ExtrudeEnd.KThroughAll
        and definition.length is None
        and definition.second_length is None
        and definition.second_end_condition is None
        and not definition.symmetric
        and not cut.parameter_ids
        and definition.reversed is False,
        "through cut requires one simple depthless effective direction",
    )
    effective = scaled(selected.frame.z_axis, -1 if selected.extent[0] < 0 else 1)
    require(
        definition.direction == effective,
        "through direction does not cover the selected stock",
    )
    require(
        {body.final_feature_id for body in document.bodies}
        == {untouched.feature_id, cut.id},
        "final bodies must retain the untouched and cut-result producers",
    )
    return ShapeIntent(
        selected,
        untouched,
        cut.id,
        choice.id,
        read_circle(sketch, scale),
        effective,
        document.bodies,
    )
