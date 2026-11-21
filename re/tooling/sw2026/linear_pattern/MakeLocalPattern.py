from dataclasses import dataclass

from convert.adapters.solidworks.Archive.Construction.Patterns.Direction.ReadPatDir import ReadPatDir
from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.MakePatGraph import MakePatGraph
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.LinPatternInput import LinPatternInput

from CheckPatternAngleOwners import require
from MakeLocalPatternDrivers import typed_styles
from MakePatternAngularPlane import AngularPlaneIntent, angle_input
from MakePatternAnnotationCatalog import annotation_inputs
from MakePatternSeed import RaisedSeedGraph, RaisedSeedIntent, stock_input
from PatternBoxGeometry import whole_solid_measure


@dataclass(frozen=True, slots=True)
class LocalPatternIntent:
    name: str
    count: int
    pitch_m: float
    reverse: bool
    styles: tuple


@dataclass(frozen=True, slots=True)
class PatternGraph:
    seed: RaisedSeedGraph
    axis: object
    plane: object
    plane_driver: object
    pattern: object
    pattern_drivers: tuple
    headers: tuple
    measure: dict

    @property
    def roots(self):
        return (*self.seed.roots, self.axis, self.plane, self.pattern)


def direction_fields(plane):
    line = ReadPatDir(plane)
    return {"fc8": line.PointValue, "fe0": line.DirectionValue, "fb0": 0.0, "fb8": line.SpanValue, "f68": 1}


def make_pattern(seed_intent, axis_name, plane_intent, annotation, pattern_intent):
    require(type(seed_intent) is RaisedSeedIntent and type(plane_intent) is AngularPlaneIntent
            and type(pattern_intent) is LocalPatternIntent and type(pattern_intent.reverse) is bool,
            "pattern requires explicit raised seed, angle constraint and signed repetition intent")
    shown = annotation["shown"]
    require(isinstance(shown, (tuple, list)), "expected an ordered bounded catalog and explicit shown view roles")
    prepared = LinPatternInput(
        stock_input(seed_intent), axis_name, angle_input(plane_intent),
        annotation_inputs(annotation["views"]), annotation["active"], tuple(shown),
        pattern_intent.name, pattern_intent.count, pattern_intent.pitch_m,
        pattern_intent.reverse, typed_styles(pattern_intent.styles),
    )
    graph = MakePatGraph(prepared)
    stock = graph.StockValue
    direction = tuple(-value if prepared.Reversed else value for value in ReadPatDir(graph.PlaneValue).DirectionValue)
    measure = whole_solid_measure(seed_intent.plate.bounds_m, seed_intent.seed.bounds_m, direction,
                                  prepared.PitchValue, prepared.CountValue)
    seed = RaisedSeedGraph(stock.SystemValue, stock.SettingsValue, stock.Allocator,
                           stock.PlateValue, stock.SeedValue, stock.BoundsValue)
    return PatternGraph(seed, graph.AxisValue, graph.PlaneValue, graph.AngleValue, graph.PatternValue,
                        graph.DriverValues, graph.HeaderValues, measure)
