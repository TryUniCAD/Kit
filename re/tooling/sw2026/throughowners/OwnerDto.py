from dataclasses import asdict, fields, replace
import json
from math import isfinite

from convert.adapters.solidworks.Archive.Construction.BodyScope.SelectedStock import SelectedStock
from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import CircleInput
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.SourceAxis import SourceAxis
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.SourceLine import SourceLine
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.SourcePlane import SourcePlane
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.SourceRefs import SourceRefs
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.ThruOwnerInput import ThruOwnerInput
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughEndInput import ThroughEndInput
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughPartSpec import ThroughPartSpec
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughStock import ThroughStock
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def safe_tree(value):
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        require(isfinite(value), "owner input contains a nonfinite scalar")
        return
    if type(value) in (list, tuple):
        for item in value:
            safe_tree(item)
        return
    require(type(value) is dict, "owner input contains a nonportable value")
    for key, item in value.items():
        require(type(key) is str and key not in ("native_fields", "metadata", "provenance", "source_bytes", "solidworks_source_bytes"), "source observation reached generation input")
        safe_tree(item)


def encode(value):
    stock = value.ShapeValue.StockValue
    result = {
        "shape": asdict(value.ShapeValue),
        "scope": {"mode": value.ScopeValue.ModeValue, "version": value.ScopeValue.VersionValue, "feature_id": stock.FeatureId, "body_id": stock.BodyId},
        "planes": [asdict(item) for item in value.PlaneValues],
        "lines": [asdict(item) for item in value.LineValues],
        "axes": [asdict(item) for item in value.AxisValues],
        "refs": asdict(value.RefsValue),
        "unit": value.UnitValue,
    }
    safe_tree(result)
    return result


def exact(value, keys):
    require(type(value) is dict and set(value) == set(keys), "owner transport has missing or unsupported fields")
    return dict(value)


def record(cls, value):
    return exact(value, (item.name for item in fields(cls) if item.init))


def decode(value):
    safe_tree(value)
    data = exact(value, ("shape", "scope", "planes", "lines", "axes", "refs", "unit"))
    shape = record(ThroughPartSpec, data["shape"])
    stock_data = record(ThroughStock, shape["StockValue"])
    stock_data["VerticesValue"] = tuple(tuple(item) for item in stock_data["VerticesValue"])
    stock = ThroughStock(**stock_data)
    circle_data = record(CircleInput, shape["CircleValue"])
    circle_data["CenterValue"] = tuple(circle_data["CenterValue"])
    shape["StockValue"] = stock
    shape["CircleValue"] = CircleInput(**circle_data)
    shape["EndValue"] = ThroughEndInput(**record(ThroughEndInput, shape["EndValue"]))
    scope = exact(data["scope"], ("mode", "version", "feature_id", "body_id"))
    require((scope["feature_id"], scope["body_id"]) == (stock.FeatureId, stock.BodyId), "selected stock transport lost its actual producer")
    refs = record(SourceRefs, data["refs"])
    refs["StockParents"], refs["CutParents"] = tuple(refs["StockParents"]), tuple(refs["CutParents"])
    return ThruOwnerInput(ThroughPartSpec(**shape), SelectedStock((stock,), scope["mode"], scope["version"]), tuple(SourcePlane(**record(SourcePlane, item)) for item in data["planes"]), tuple(SourceLine(**record(SourceLine, item)) for item in data["lines"]), tuple(SourceAxis(**record(SourceAxis, item)) for item in data["axes"]), SourceRefs(**refs), data["unit"])


def settings(value, written_at):
    result = MakePartRecipe(value.ShapeValue.StockValue, written_at)
    require(value.UnitValue == "mm", "this proof uses declared millimetre target settings only")
    return replace(result, SystemValue=replace(result.SystemValue, PlaneNames=tuple((item.AxisValue, item.NameValue) for item in value.PlaneValues)))
