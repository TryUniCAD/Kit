from dataclasses import dataclass
from math import dist
from struct import pack

from builders.Extrude import common_display_fields
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import DimensionGraph
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeDistTail import MakeDistTail
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeHandleMut import MakeHandleMut
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeTextFields import MakeTextFields
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeValueFields import MakeValueFields
from convert.adapters.solidworks.Archive.Construction.Dimensions.ReadModelLinear import ReadModelLinear
from convert.adapters.solidworks.Archive.Construction.Nodes.InitNodeMut import InitNodeMut

from CheckPatternAngleOwners import annotation_catalog, matrix, require
from MakePatternAngularPlane import typed_node
from MakePatternAnnotationCatalog import UNASSIGNED_ANNOTATIONS, display_membership
from MakePatternPrincipalDisplay import point
from PatternAngleGeometry import offsets
from PatternHingeGeometry import ORIGIN
from PatternPlaneDirectionRule import dot


DRIVER_SLOTS = (
    ("f1258", "D1", True),
    ("f1260", "D3", False),
    ("f1268", "D2", True),
    ("f1270", "D4", False),
    ("f1318", "D5", False),
    ("f1320", "D6", False),
)


@dataclass(frozen=True, slots=True)
class PatternDriverStyle:
    name: str
    annotation_view: str | None
    label_m: tuple[float, float, float]
    design_intent: bool
    selected_leader: int


def check_styles(styles):
    require(type(styles) is tuple and len(styles) == len(DRIVER_SLOTS)
            and all(type(style) is PatternDriverStyle for style in styles),
            "pattern requires six explicitly styled driving or dormant display owners")
    for style, (_, name, _) in zip(styles, DRIVER_SLOTS, strict=True):
        require(style.name == name and type(style.label_m) is tuple and len(style.label_m) == 3
                and all(type(value) is float and abs(value) < 1e3 for value in style.label_m) and style.label_m[2] == 0.0
                and type(style.design_intent) is bool and type(style.selected_leader) is int
                and -(1 << 31) <= style.selected_leader < (1 << 31)
                and style.annotation_view == ("*Back" if name == "D1" else None)
                and (name != "D3" or style.label_m == ORIGIN),
                "pattern display style is outside the oblique Back count and unassigned pitch profile")


def driver_views(root, style):
    if style.name == "D1":
        selection = display_membership(root, style.annotation_view)["f2b0"]
        require([matrix(row["f368"]) for row in annotation_catalog(root) if row["f360"] == selection[0]["v"]]
                == [((-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0))],
                "pattern count display requires the actual canonical Back annotation frame")
        return selection
    if style.name == "D3":
        return ({"v": UNASSIGNED_ANNOTATIONS},)
    return ()


def numeric_driver(owner, style, value, display_id, is_count, root, witnesses, linear):
    param = typed_node("moIntegerParameter_c" if is_count else "moLengthParameter_c", {})
    InitNodeMut(param, style.name)
    param.FieldsValue.update(owner=owner, f0c=0, f48=None, f58=value, **{"f60" if is_count else "f68": 0})
    dimension = typed_node("moNumberDim_c" if is_count else "ParallelPlaneDistanceDim_c", MakeValueFields(owner, param))
    handle = MakeHandleMut(owner, dimension)
    fields = common_display_fields(handle=handle, angular=False, design_intent=style.design_intent,
                                   selected_leader=style.selected_leader)
    fields.update(owner=owner, f58=display_id, f2b0=driver_views(root, style))
    fields["f6a0"] = {**MakeTextFields(18), "f10": 0 if is_count else 18, "f38": point(style.label_m)}
    fields["f5b0"]["data"] = pack("<d", value if display_id else 0.0)
    if not is_count:
        fields.update(MakeDistTail())
        fields.update(linear.ProjectionValue)
        fields["fb64"] = (fields["fb64"] & ~0x103000) | linear.FlagValue
        fields["f8a4"] = (fields["f8a4"] & ~0x50) | linear.UnderText
    if style.name == "D1":
        fields["fad0"] = float(value)
    if style.name == "D3":
        start, finish = witnesses
        span = dist(start, finish)
        require(span > 0.0, "pitch display must retain distinct actual witness positions")
        delta = tuple(b - a for a, b in zip(start, finish, strict=True))
        midpoint = offsets(start, delta, 0.5)
        relative = tuple(a - b for a, b in zip(midpoint, start, strict=True))
        dimension.FieldsValue.update(f80=point(start), fa0=point(finish), fc0=point(ORIGIN))
        fields.update(f880=point((0.0, 1.0, 0.0)), fa38=point((1.0, 0.0, 0.0)), f988=point((span, 0.0, 0.0)),
                      f9a0=point((span, 0.0, 0.0)), fad0=span, f8a8=dot(relative, delta) / dot(delta, delta))
    display = typed_node("moDisplayDim_c" if is_count else "moDisplayDistanceDim_c", fields)
    return DimensionGraph(param, dimension, handle, display)


def make_drivers(owner, root, styles, count, pitch, witnesses, allocator):
    values = count, pitch, 1, 0.0, 0.0, 0.0
    model_fields = root.FieldsValue
    display_id = model_fields["fd44"]
    require(type(display_id) is int and 0 < display_id < 0x7FFFFFFE, "pattern requires two actual model display IDs")
    registered = {"D3": display_id, "D1": display_id + 1}
    linear = ReadModelLinear(root)
    drivers = tuple(numeric_driver(owner, style, value, registered.get(name, 0), is_count, root, witnesses, linear)
                    for style, value, (_, name, is_count) in zip(styles, values, DRIVER_SLOTS, strict=True))
    for (slot, _, _), graph in zip(DRIVER_SLOTS, drivers, strict=True):
        allocator.AllocateMut(graph.DimensionValue, "f50")
        owner.FieldsValue[slot] = graph.DisplayValue
    model_fields["fd44"] = display_id + len(registered)
    return drivers
