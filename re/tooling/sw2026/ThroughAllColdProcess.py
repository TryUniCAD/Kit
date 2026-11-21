from base64 import b64decode, b64encode
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys
from xml.etree.ElementTree import fromstring

root = Path(sys.argv[1]).resolve()
phase = sys.argv[2]
sys.path[:0] = [str(root), str(root / "src"), str(Path(__file__).parent)]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

audit = BuildAudit(root / "re/tooling/sw2026/serial/defs")
sys.addaudithook(audit.InspectEvent)

from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import CircleInput
from convert.adapters.solidworks.Archive.Construction.ThroughAll.MakeThroughEnd import MakeThroughEnd
from convert.adapters.solidworks.Archive.Construction.ThroughAll.MakeThroughPart import MakeThroughPart
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughEndInput import ThroughEndInput
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughPartSpec import ThroughPartSpec
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughStock import ThroughStock
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from SdkNativeRoundTrips import roundtrips


def require(value, message):
    if not value:
        raise ValueError(message)


def read_input(request):
    keys = {"name", "configuration", "axis", "stock_size_m", "stock_center_m", "circle_center_m", "radius_m", "direction", "native_path", "written_at"}
    require(set(request) == keys, "through-all research request has unsupported or missing intent")
    require(request["direction"] in ("forward", "reverse", "both"), "unsupported through-all direction")
    width, height, depth = request["stock_size_m"]
    cx, cy = request["stock_center_m"]
    vertices = ((cx-width/2, cy-height/2), (cx+width/2, cy-height/2), (cx+width/2, cy+height/2), (cx-width/2, cy+height/2))
    axis = request["axis"]
    plane = {"x": "Right Plane", "y": "Top Plane", "z": "Front Plane"}[axis]
    plan = ThroughStock(request["name"], request["configuration"], plane, "stock-sketch", "StockProfile", "stock-boss", "StockBoss", "stock-depth", "cut-body", vertices, depth, width, height, axis)
    circle = CircleInput(tuple(request["circle_center_m"]), request["radius_m"], 19000)
    end = ThroughEndInput("through_all_both" if request["direction"] == "both" else "through_all", request["direction"] != "reverse", 19000)
    return ThroughPartSpec(plan, circle, "ThroughProfile", "ThroughFeature", end)


def param(display):
    handle = display.FieldsValue["f850"][0]["o"]
    dimension = handle.FieldsValue["ff0"]
    value = dimension.FieldsValue["f28"]
    return {"id": dimension.FieldsValue["f50"], "name": ReadNodeName(value), "value": value.FieldsValue["f58"]}


def inspect(archive, linked, expected):
    features = linked.ResolvedValue.RootsValue
    named = {ReadNodeName(node): node for node in features}
    require(len(named) == len(features), "generated native feature names are not unique")
    stock, boss, circle, cut = (named[key] for key in ("StockProfile", "StockBoss", "ThroughProfile", "ThroughFeature"))
    require(features[-4:] == (stock, boss, circle, cut), "ordered through-all feature history differs")
    require(cut.ClassValue.NameValue == "moICE_c" and cut.FieldsValue["f810"] == 1, "through-all operation is not an actual native cut")
    for extrude, profile in ((boss, stock), (cut, circle)):
        require(extrude.FieldsValue["f60"]["list"]["items"][0]["o"] is profile, "native extrusion dependency lost its actual sketch")
    end = cut.FieldsValue["f818"].FieldsValue
    both = expected.EndValue.ModeValue == "through_all_both"
    values = (int(not both), 1, int(both), 0, int(expected.EndValue.IsReversed))
    require(tuple(end[key] for key in ("f08", "f0c", "f10", "f88", "f8c")) == values, "through-all first/second type or reversal differs")
    require(all(end[key] is None for key in ("f18", "f20", "fc8", "fd0", "f138", "f90")) and end["f140"].FieldsValue["t"] == 0, "depth-less end acquired an unused owner")
    require(all(end[key] == 0 for key in ("f150", "f154", "f158")), "fresh end lifecycle inherited saved tail words")
    require(all(cut.FieldsValue[key] == 0 for key in ("f544", "has_f528", "has_f530", "has_f548", "has_f4c0")) and cut.FieldsValue["f538"] is None, "fresh cut acquired captured body scope")
    stock_end = boss.FieldsValue["f818"].FieldsValue
    require(stock_end["f0c"] == 6 and stock_end["f08"] == 1, "stock must retain its total mid-plane termination")
    depth = param(stock_end["f18"])
    require(depth["name"] == "D1" and depth["value"] == expected.StockValue.DepthValue, "stock total driving depth differs")
    rows = list(fromstring(archive.require("swXmlContents/KeyWords")[1:]))[-4:]
    require(tuple(row.attrib["Name"] for row in rows) == ("StockProfile", "StockBoss", "ThroughProfile", "ThroughFeature"), "keyword feature identity differs")
    require(len(rows[0]) == len(rows[2]) == len(rows[3]) == 0 and len(rows[1]) == 1, "keywords invented sketch or cut dimensions")
    require(rows[3].attrib["DissectableChildren"] == str(circle.FieldsValue["f08"]), "cut keyword lost its actual profile dependency")
    return {"feature_ids": {key: named[key].FieldsValue["f08"] for key in ("StockProfile", "StockBoss", "ThroughProfile", "ThroughFeature")}, "end_tuple": values, "stock_depth": depth, "cut_depth_owners": 0, "cut_draft_owners": 0, "saved_tail_values_used": False}


def main(request):
    expected = read_input(request["recipe"] if phase == "audit" else request)
    if phase == "build":
        settings = MakePartRecipe(expected.StockValue, request["written_at"])
        settings = replace(settings, OutputValue=replace(settings.OutputValue, PathName=request["native_path"]))
        candidate = MakeThroughPart(expected, settings)
        require(candidate.CutValue.DepthValue is None, "through-all cut allocated a dimensional graph")
        require(candidate.CutValue.FeatureValue.FieldsValue["owner"] is candidate.SystemValue.RootValue and candidate.CutValue.ProfileValue.ProfileValue.FieldsValue["owner"] is candidate.SystemValue.RootValue, "constructed cut and circle lost their actual root owner")
        geometry = candidate.ProfileValue.GeometryValue.SketchValue.FieldsValue["dims"]
        require(geometry["nlog1"] == 4 and geometry["ng2"] == 0, "stock relation intent differs")
        require(geometry["f118"].FieldsValue["n"] == 0, "axis-only stock acquired display dimensions")
        data = candidate.BytesValue
    elif phase == "audit":
        data = b64decode(request["generated"], validate=True)
    else:
        raise ValueError("expected build or audit phase")
    archive = SldprtArchive.from_bytes(data)
    linked, _, _, _, streams = roundtrips(archive, False)
    grammar = inspect(archive, linked, expected)
    require(BuildSldprt({row.name: row.data for row in archive.records}, FormatVersion=4) == data, "generated complete container changed on repack")
    research = [name for name, module in tuple(sys.modules.items()) if name not in ("__main__", "SdkNativeRoundTrips") and str(getattr(module, "__file__", "")).startswith(str(root / "re") + "/")]
    require(not audit.DeniedReads and not research, "SDK constructor used runtime file or research inputs")
    result = {"passed": True, "phase": phase, "sha256": sha256(data).hexdigest(), "bytes": len(data), "streams": streams, "grammar": grammar, "runtime_input_file_reads": len(audit.DeniedReads), "sdk_runtime_research_imports": len(research), "native_acceptance": False, "public_writer_qualified": False}
    if phase == "build":
        result["generated"] = b64encode(data).decode("ascii")
    return result


codecs = tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
request = json.load(sys.stdin)
audit.BeginBuild()
print(json.dumps(main(request), sort_keys=True, allow_nan=False))
