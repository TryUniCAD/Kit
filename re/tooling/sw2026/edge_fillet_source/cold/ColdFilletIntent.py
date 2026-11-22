from dataclasses import dataclass, replace
from math import isfinite

from FilletModel import edge_role, require, stock

from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfPlan import ChmfEdgePlan
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureKinds import FilletFeature
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordParameter import ParameterValue
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import MakePlainDoc

FEATURE_NAME = "ConstantEdgeFillet"
SKETCH_NAME = "FilletStockSketch"
STOCK_NAME = "FilletStockBoss"


@dataclass(frozen=True, slots=True)
class ColdFilletIntent:
    document: CadDocument
    edge: ChmfEdgePlan
    definition: FilletFeature
    locator: SelfFileInput


def prepare_intent(spec, locator):
    require(set(spec) == {"name", "size_mm", "center_mm", "edge_axis", "corner", "radius_mm"},
            "expected only neutral fillet intent")
    size, center, radius = spec["size_mm"], spec["center_mm"], spec["radius_mm"]
    require(len(size) == 3 and len(center) == 2
            and all(type(value) in (float, int) and isfinite(value) for value in (*size, *center, radius))
            and all(0.001 <= value <= 300.0 for value in size), "expected finite bounded neutral stock geometry and radius")
    plain = MakePlainDoc(spec["name"], *size)
    (profile,) = plain.sketches
    cx, cy = spec["center_mm"]

    def translate(point):
        return PlaneVector(point.x + cx, point.y + cy)

    entities = tuple(replace(entity, geometry=LineGeometry(translate(entity.geometry.start), translate(entity.geometry.end)))
                     for entity in profile.entities)
    sketch = replace(profile, name=SKETCH_NAME, entities=entities)
    (before,) = plain.feature_timeline
    boss = replace(before, name=STOCK_NAME)
    body = replace(plain.bodies[0], name=STOCK_NAME)
    document = replace(plain, sketches=(sketch,), feature_timeline=(boss,), bodies=(body,),
                       configurations=(replace(plain.configurations[0], name="Default"),))
    sizes, bounds = stock(spec)
    _, axis, transverse, _, _ = edge_role(spec)
    side = spec["corner"]
    if axis == 2 and side == {"x": "max", "y": "min"}:
        carrier = 0
    elif axis == 0 and side == {"y": "max", "z": "max"}:
        carrier = 2
    else:
        raise ValueError("stock positive-fin selection needs a measured carrier orientation")
    corner = tuple(int(side.get(name) == "max") for name in "xyz")
    span = min(sizes[index] for index in transverse)
    radius = spec["radius_mm"] / 1000.0
    require(1e-14 <= radius < span / 2.0, "uniform radius exceeds its convex stock supports")
    edge = ChmfEdgePlan(bounds, axis, carrier, corner, span)
    return ColdFilletIntent(document, edge, FilletFeature(ParameterValue(radius, ValueKind.KLength, "m")), locator)
