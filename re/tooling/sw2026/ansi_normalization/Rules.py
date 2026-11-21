from copy import deepcopy

from SpatialTextMut import concrete, require
from convert.adapters.solidworks.Archive.Construction.Styles.MakeSwiftOpts import (
    MakeSwiftOpts,
)
from convert.adapters.solidworks.Archive.Construction.Units.MakeDualLength import (
    MakeDualLength,
)
from convert.adapters.solidworks.Archive.Construction.Units.MakeUnitFields import (
    MakeUnitFields,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput

LENGTH_CHILDREN = ("fe0", "f2f8", "f3f8", "f500", "f608", "f830", "f960", "fa68")
METRIC_MINIMUM_TWO = (
    "f30",
    "ff0",
    "f100",
    "f118",
    "f128",
    "f210",
    "f158",
    "f168",
    "f220",
    "f2c8",
    "f2d8",
    "f2e0",
)
METRIC_MINIMUM_ONE = (
    "f40",
    "f50",
    "fe0",
    "f60",
    "f70",
    "f198",
    "f1a8",
    "f230",
    "fc0",
    "fd0",
    "fa0",
    "fb0",
    "f108",
    "f138",
    "f148",
    "f218",
    "f1b8",
    "f1c8",
    "f238",
    "f178",
    "f188",
    "f228",
    "f2f0",
    "f300",
    "f308",
    "f318",
    "f328",
    "f330",
    "f340",
    "f350",
    "f358",
    "f368",
    "f378",
    "f380",
    "f1d8",
    "f1e8",
    "f1f8",
    "f208",
    "f258",
    "f268",
    "f278",
    "f288",
    "f298",
    "f2a8",
    "f390",
    "f398",
    "f388",
    "f240",
    "f248",
)


def primary_units(model, inputs):
    require(type(inputs) is UnitInput, "normalization needs actual semantic units")
    require(
        inputs.LengthUnit == "mm" and inputs.AngleUnit == "degree",
        "normalization experiment admits millimetres and degrees only",
    )
    table = concrete(model.FieldsValue["f9b8"], "moUnitsTable_c")
    rows = table.FieldsValue["items"]
    require(table.FieldsValue["n"] == len(rows) == 16, "actual unit factory differs")
    result = []
    for name in ("moLengthUserUnits_c", "moAngleUserUnits_c"):
        found = [row["o"] for row in rows if row["o"].ClassValue.NameValue == name]
        require(len(found) == 1, "unit table needs one actual primary owner")
        unit = concrete(found[0], name)
        require(
            unit.FieldsValue["fb0"] == 0
            and unit.FieldsValue["f0c"] == inputs.DecimalPlaces,
            "actual unit owner disagrees with independently authored settings",
        )
        kind = "length" if name == "moLengthUserUnits_c" else "angle"
        require(
            unit.FieldsValue == MakeUnitFields(kind, 0, inputs.DecimalPlaces),
            "normalization only owns fresh semantic unit construction",
        )
        result.append(unit)
    require(
        result[0].FieldsValue["fb8"] is None, "fresh primary has another dual owner"
    )
    return result


def precision(value):
    require(type(value) is int and 0 <= value <= 16, "style precision is unsupported")
    return min(value, 16)


def synchronize_units(details, length, angle):
    dimensions = details["f13b0"]
    for key in LENGTH_CHILDREN:
        dimension = dimensions[key]
        unit = deepcopy(length.FieldsValue)
        unit["f0c"] = precision(dimension["f80"])
        dual = MakeDualLength("mm")
        dual.FieldsValue["f0c"] = precision(dimension["f84"])
        unit["fb8"] = dual
        dimension["ff0"] = unit
    for key in ("f1f0", "f830", "fa68"):
        unit = deepcopy(angle.FieldsValue)
        if key != "fa68":
            field = "f108" if key == "f830" else "f80"
            unit["f0c"] = precision(dimensions[key][field])
        dimensions[key]["ff8"] = unit


def initialize_swift(details, length):
    swift = details["ff68"]
    require(swift == MakeSwiftOpts(), "normalization requires fresh metric Swift state")
    places = precision(length.FieldsValue["f0c"])
    for field in METRIC_MINIMUM_TWO:
        swift[field] = max(places, 2)
    for field in METRIC_MINIMUM_ONE:
        swift[field] = max(places, 1)
    swift["f10"] = 1


def initialize_model(model, inputs):
    model = concrete(model, model.ClassValue.NameValue)
    require(
        model.ClassValue.NameValue in ("moPart_c", "moDrawing_c")
        and model.ClassValue.SchemaValue == 1,
        "normalization needs a fresh concrete part or drawing owner",
    )
    details = model.FieldsValue["fae0"]
    require(
        type(details["n58"]) is int
        and details["n58"] == len(details["f58"])
        and details["n58"] > 0,
        "normalization experiment requires explicit nonempty authored exclusions",
    )
    length, angle = primary_units(model, inputs)
    synchronize_units(details, length, angle)
    initialize_swift(details, length)
