from dataclasses import dataclass, replace
from math import acos, atan2, dist, fsum, isclose, isfinite, pi, sqrt

from convert.Formats.Fusion.Revolves.JoinRevModels import JoinRevModels
from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.Geometry.Extrude.Polygon.PrismFrame import PlacePrismPoint
from convert.Geometry.Extrude.Trimmed.TrimMeasures import ArcArea
from convert.Geometry.Extrude.Trimmed.TrimPrism import BuildTrimPrism
from convert.Geometry.Revolve.SweepVector import DotVector
from convert.adapters.solidworks.Core.TypedResolved.Circles.LocalCircle import (
    LocalCircle,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.BuildCircularCut import (
    BuildCircleCut,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Features.FeatureBody import DesignBody
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.GeometryCurves import (
    ArcGeometry,
    CircleGeometry,
    LineGeometry,
)
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordTopology import TopologyCounts

from ShapeIntent import Stock, project_intent, require, xyz


@dataclass(frozen=True)
class SolidShape:
    brep: BrepModel
    topology: TopologyCounts
    center_mm: SpaceVector


@dataclass(frozen=True)
class TwoStockShape:
    brep: BrepModel
    bodies: tuple[DesignBody, DesignBody]
    solids: tuple[SolidShape, SolidShape]
    selected_stock: SolidShape
    selected_producer: str
    untouched_producer: str
    result_producer: str
    selection_id: str
    untouched_cutter_overlap: bool
    volume_mm3: float
    area_mm2: float
    center_mm: SpaceVector


def stock_lines(stock):
    return tuple(
        LineGeometry(start, end)
        for start, end in zip(
            stock.corners, (*stock.corners[1:], stock.corners[0]), strict=True
        )
    )


def stock_center(stock):
    first, _, opposite, _ = stock.corners
    return PlaneVector((first.x + opposite.x) / 2, (first.y + opposite.y) / 2)


def checked_solid(body_id, stock, projected, center_xy):
    brep, volume, area, bounds = projected
    require(
        len(brep.bodies) == len(brep.regions) == len(brep.shells) == 1
        and brep.regions[0].solid
        and brep.shells[0].closed
        and brep.bodies[0].design_body_id == body_id,
        "cold model did not produce one closed solid for its actual body",
    )
    center = PlacePrismPoint(stock.frame, center_xy, sum(stock.extent) / 2)
    require(
        all(isfinite(value) for value in (volume, area, *xyz(center)))
        and min(volume, area) > 0,
        "cold solid mass properties exceed the supported range",
    )
    topology = TopologyCounts(
        solid_count=1,
        shell_count=1,
        face_count=len(brep.faces),
        edge_count=len(brep.edges),
        vertex_count=len(brep.vertices),
        volume=volume,
        surface_area=area,
        bounding_box=bounds,
        valid=True,
    )
    normalized = replace(brep, bodies=(replace(brep.bodies[0], id=f"{body_id}:brep"),))
    return SolidShape(normalized, topology, center)


def build_stock(stock, body_id):
    return checked_solid(
        body_id,
        stock,
        BuildPrism(body_id, stock.frame, stock_lines(stock), *stock.extent),
        stock_center(stock),
    )


def project_circle(stock, circle, body_id):
    first, _, last, _ = stock.corners
    x, y, radius = circle.center.x, circle.center.y, circle.radius
    if (
        first.x < x - radius < x + radius < last.x
        and first.y < y - radius < y + radius < last.y
    ):
        plan = PrismPlan(
            stock.frame, stock_lines(stock), stock.extent[1] - stock.extent[0], {}
        )
        tool = LocalCircle((x, y), radius, 0, 0, None, None, {})
        projected = BuildCircleCut(
            plan, tool, stock.extent, stock.extent, body_id, f"{body_id}-through"
        )
        return (
            (
                projected.BrepValue,
                projected.TopologyValue.volume,
                projected.TopologyValue.surface_area,
                projected.TopologyValue.bounding_box,
            ),
            pi * radius**2,
            circle.center,
        )
    lines, removed_area, removed_center = notch_ring(stock, circle)
    return (
        BuildTrimPrism(body_id, stock.frame, lines, *stock.extent),
        removed_area,
        removed_center,
    )


def notch_ring(stock, circle):
    lines = stock_lines(stock)
    center, radius = circle.center, circle.radius
    edges = []
    for index, line in enumerate(lines):
        origin, end = line.start, line.end
        length = dist((origin.x, origin.y), (end.x, end.y))
        tx, ty = (end.x - origin.x) / length, (end.y - origin.y) / length
        nx, ny = -ty, tx
        x, y = center.x - origin.x, center.y - origin.y
        outward = -(x * nx + y * ny)
        if outward > 0:
            edges.append((index, outward, x * tx + y * ty, length, (tx, ty), (nx, ny)))
    require(
        len(edges) == 1 and edges[0][1] < radius,
        "circular through cut requires one enclosed hole or one proper exterior side notch",
    )
    index, outward, station, length, (tx, ty), (nx, ny) = edges[0]
    origin, end = lines[index].start, lines[index].end
    half = sqrt((radius - outward) * (radius + outward))
    back = lines[index - 1].start
    inward_depth = dist((back.x, back.y), (origin.x, origin.y))
    require(
        0 < station - half < station + half < length
        and radius - outward < inward_depth,
        "circular notch crosses a corner, touches a wall or cuts multiple stock sides",
    )
    enter = PlaneVector(
        origin.x + tx * (station - half), origin.y + ty * (station - half)
    )
    leave = PlaneVector(
        origin.x + tx * (station + half), origin.y + ty * (station + half)
    )
    angle = atan2(leave.y - center.y, leave.x - center.x)
    arc = ArcGeometry(center, radius, angle, angle + 2 * acos(outward / radius))
    area = ArcArea(arc)
    require(
        isfinite(area) and area > 0.0,
        "circular notch has no representable removed area",
    )
    displacement = (2.0 / 3.0) * half**3 / area
    removed_center = PlaneVector(
        center.x + nx * displacement, center.y + ny * displacement
    )
    ring = (
        *lines[:index],
        LineGeometry(origin, enter),
        arc,
        LineGeometry(leave, end),
        *lines[index + 1 :],
    )
    return ring, area, removed_center


def trimmed_stock(stock, circle, body_id, original):
    projected, loss, removed_center = project_circle(stock, circle, body_id)
    height = stock.extent[1] - stock.extent[0]
    face_area = original.topology.volume / height
    remaining = face_area - loss
    require(
        remaining > 0
        and isclose(projected[1], remaining * height, rel_tol=1e-10, abs_tol=1e-9),
        "computed cut material does not match its analytic removed section",
    )
    intact_center = stock_center(stock)
    ratio = loss / remaining
    center = PlaneVector(
        intact_center.x + ratio * (intact_center.x - removed_center.x),
        intact_center.y + ratio * (intact_center.y - removed_center.y),
    )
    return checked_solid(body_id, stock, projected, center)


def body_ranges(bounds):
    return tuple(zip(xyz(bounds.minimum), xyz(bounds.maximum), strict=True))


def check_disjoint(first, second):
    require(
        any(
            a_max < b_min or b_max < a_min
            for (a_min, a_max), (b_min, b_max) in zip(
                body_ranges(first), body_ranges(second), strict=True
            )
        ),
        "the two original stocks must have positive separation",
    )


def untouched_overlap(bounds, selected, circle, direction):
    corners = tuple(
        SpaceVector(x, y, z)
        for x in body_ranges(bounds)[0]
        for y in body_ranges(bounds)[1]
        for z in body_ranges(bounds)[2]
    )
    relative = tuple(
        SpaceVector(
            *(
                value - origin
                for value, origin in zip(
                    xyz(corner), xyz(selected.frame.origin), strict=True
                )
            )
        )
        for corner in corners
    )
    if max(DotVector(point, direction) for point in relative) <= 0:
        return False
    distances = []
    for axis, center in zip(
        (selected.frame.x_axis, selected.frame.y_axis),
        (circle.center.x, circle.center.y),
        strict=True,
    ):
        values = tuple(DotVector(point, axis) for point in relative)
        distances.append(max(min(values) - center, center - max(values), 0.0))
    return distances[0] ** 2 + distances[1] ** 2 < circle.radius**2


def build_two_stock_shape(document):
    intent = project_intent(document)
    originals = {body.final_feature_id: body for body in intent.bodies}
    moving = originals[intent.untouched.feature_id]
    result = originals[intent.cut_id]
    selected = build_stock(
        intent.selected, f"{intent.selected.feature_id}:historical-stock"
    )
    untouched = build_stock(intent.untouched, moving.id)
    check_disjoint(selected.topology.bounding_box, untouched.topology.bounding_box)
    cut = trimmed_stock(intent.selected, intent.circle, result.id, selected)
    by_producer = {intent.untouched.feature_id: untouched, intent.cut_id: cut}
    solids = tuple(by_producer[body.final_feature_id] for body in intent.bodies)
    brep = JoinRevModels(tuple(solid.brep for solid in solids))
    bodies = tuple(
        replace(body, topology=solid.topology)
        for body, solid in zip(intent.bodies, solids, strict=True)
    )
    errors = brep.validate(frozenset(body.id for body in bodies))
    require(
        not errors,
        "composed stock solids violate body or topology ownership: "
        + "; ".join(errors),
    )
    volume = sum(solid.topology.volume for solid in solids)
    area = sum(solid.topology.surface_area for solid in solids)
    require(
        isfinite(volume) and isfinite(area),
        "combined stock measures exceed the supported range",
    )
    center = SpaceVector(
        *(
            fsum(
                (solid.topology.volume / volume) * getattr(solid.center_mm, coord)
                for solid in solids
            )
            for coord in ("x", "y", "z")
        )
    )
    overlap = untouched_overlap(
        untouched.topology.bounding_box,
        intent.selected,
        intent.circle,
        intent.cutter_direction,
    )
    return TwoStockShape(
        brep,
        bodies,
        solids,
        selected,
        intent.selected.feature_id,
        intent.untouched.feature_id,
        intent.cut_id,
        intent.selection_id,
        overlap,
        volume,
        area,
        center,
    )
