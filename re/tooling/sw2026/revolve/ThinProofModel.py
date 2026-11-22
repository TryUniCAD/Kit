from math import radians

from interchange import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.ThinRevolve import ThinRevolve
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Selection import SelectPathElem, Selection
from interchange.geometry.Models.Sketch import Sketch, SketchEntity
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector

WALL_MODES = {"one": "one_sided", "opposite": "opposite", "midplane": "midplane", "two": "two_sided"}
FEATURE = "feature/revolve"


def world(case, point):
    x, y, z = point
    return {"front": (x, y, z), "top": (x, z, -y), "right": (z, y, -x)}[case["plane"]]


def neutral(case):
    def line(identity, x, span, construction=False):
        start, end = (PlaneVector(x * 1000, y * 1000) for y in span)
        return SketchEntity(
            identity, GeometryKind.KLine, LineGeometry(start, end), construction=construction
        )

    def driver(dimension, value, kind, unit):
        return Parameter(
            f"parameter/{dimension}", dimension, ParameterValue(value, kind, unit),
            ParameterRole.KDriving, owner_id=FEATURE,
        )

    assert not case["reverse"]
    x = case["axis_x_m"]
    axis = line("axis/centre", x, case["axis_axial_m"], True)
    wall = line("profile/open", x + case["profile_radius_m"], case["axial_m"])
    basis = ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))
    plane = SupportPlane(
        "plane/profile", case["plane"].title() + " Plane",
        Transform(*(SpaceVector(*world(case, vector)) for vector in basis)),
    )
    sketch = Sketch("sketch/profile", "RevolveSketch", plane.id, (wall, axis))
    selection = Selection("selection/axis", "Selected construction axis", (
        SelectPathElem("sketch", sketch.id), SelectPathElem("sketch_entity", axis.id),
    ))
    drivers = (
        driver("D1", radians(case["angle_deg"]), ValueKind.KAngle, "rad"),
        *(driver(name, width * 1000, ValueKind.KLength, "mm")
          for name, width in zip(("D3", "D4"), case["wall_m"][:2 if case["wall_mode"] == "two" else 1])),
    )
    start = axis.geometry.start
    sweep = AngularRevolve(
        selection.id, drivers[0].id,
        SpaceVector(*world(case, (start.x, start.y, 0))),
        SpaceVector(*world(case, (0, 1, 0))),
    )
    feature = FeatureStep(
        FEATURE, "ThinBossRevolve", FeatureKind.KRevolution, 0,
        sketch_id=sketch.id, parameter_ids=tuple(value.id for value in drivers),
        operation=BooleanOp.KCreate, selection_ids=(selection.id,),
        definition=ThinRevolve(sweep, WALL_MODES[case["wall_mode"]], *(value.id for value in drivers[1:])),
    )
    return CadDocument(
        CadSource("kit-neutral", "<authored-thin-research>", "0" * 64),
        (Configuration("configuration/default", "Default", True),), drivers, (plane,),
        (sketch,), (selection,), (feature,), (DesignBody("body/revolve", feature.name, feature.id),),
        metadata={"name": case["name"]}, units=UnitSystem.KMillimeter,
    )
