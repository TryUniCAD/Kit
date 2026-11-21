from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[2]
sys.path[:] = [value for value in sys.path if Path(value or ".").resolve() != TOOLS]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
sys.path.append(str(TOOLS))

from base64 import b64decode
from hashlib import sha256
import json

from EpochClocks import ClockPlan, drawing_clocks, require
from EpochReadback import concrete, observe_header, observe_history, require_clocks
from OriginChildShape import inspect_child
from OriginPairChecks import check_display
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHeader import ReadMgrHeader
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import WriteMgrHeader
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.History.ReadHistMut import ReadHistMut
from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Drawing.Definition.Named.ReadNamedDef import ReadNamedDef
from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import WriteNamedDef


def artifact(result, prefix):
    value = b64decode(result[prefix + "_base64"], validate=True)
    require(len(value) == result[prefix + "_bytes"] and sha256(value).hexdigest() == result[prefix + "_sha256"],
            "epoch preparation input custody differs")
    return SldprtArchive.from_bytes(value)


def history(archive):
    data = archive.require("_MO_VERSION_19000/History")
    graph = ReadHistMut(data, 19000)
    require(WriteHistMut(graph.RootValue, 19000)[0] == data, "epoch History byte identity differs")
    return observe_history(graph.RootValue)


def main():
    incoming = json.load(sys.stdin)
    require(type(incoming) is dict and set(incoming) == {"request", "build"}, "epoch preparation envelope differs")
    request, result = incoming["request"], incoming["build"]
    require(result["schema"] == "kit.sw2026.sdk-epoch-pair-result.v1" and result["passed"] is True
            and request["case"] == result["case"], "epoch preparation requires a completed fresh build")
    expected = ClockPlan.from_data(request["clock_plan"]).to_data()
    drawing_expected = drawing_clocks(request["drawing_clock_plan"])
    child_archive, drawing_archive = artifact(result, "child"), artifact(result, "drawing")
    child = ReadNativeLink(child_archive, 0)
    model = concrete(child.ConfigValue.RootValue, "moPart_c")
    header = child.ConfigValue.HeaderValue
    top = ReadHeaderGraph(child_archive.require("Header2"), 19000)
    manager = ReadMgrHeader(child_archive.require("Contents/CMgrHdr2"), 19000)
    hist = history(child_archive)
    child_clocks = require_clocks(observe_header(header, model), hist, manager.RootValue, expected)
    top_clocks = require_clocks(observe_header(top, model), hist, manager.RootValue, expected)
    cmgr = ReadCmgrMut(child_archive.require("Contents/CMgr"), 19000)
    config_bytes, config = WriteConfigMut(model, 19000, header)
    resolved_bytes, _ = WriteResolMut(child.ResolvedValue.RootsValue, child.ResolvedValue.ExtraFields,
                                     19000, config.MapValue, MakeLinkContext(child.ConfigValue, cmgr))
    roundtrips = {
        "Header2": WriteHeadGraph(top, 19000),
        "Contents/Config-0-ModelHeader": WriteHeadGraph(header, 19000),
        "Contents/Config-0": config_bytes,
        "Contents/Config-0-ResolvedFeatures": resolved_bytes,
        "Contents/CMgr": WriteCmgrMut(cmgr.RootValue, 19000),
        "Contents/CMgrHdr2": WriteMgrHeader(manager.RootValue, 19000)[0],
    }
    require(all(value == child_archive.require(name) for name, value in roundtrips.items()),
            "epoch child linked stream bytes or aliases changed")
    loaded = ReadNamedDef(drawing_archive.require("Contents/Definition"), 19000, result["orientation"])
    require(WriteNamedDef(loaded.GraphValue).OutputValue == drawing_archive.require("Contents/Definition"),
            "epoch drawing Definition byte identity differs")
    drawing_model = concrete(loaded.GraphValue.DocumentValue.FieldsValue["model"], "moDrawing_c")
    drawing_header = concrete(drawing_model.FieldsValue["fa8"], "moHeader_c")
    drawing_top = ReadHeaderGraph(drawing_archive.require("Header2"), 19000)
    drawing_hist = history(drawing_archive)
    drawing_rows = {}
    for label, value in (("inline_model_header", drawing_header), ("Header2", drawing_top)):
        observed = observe_header(value, drawing_model)
        projected = {key: observed[key] for key in drawing_expected if key != "VersionHistoryFirstEventAt"}
        projected["VersionHistoryFirstEventAt"] = drawing_hist["VersionHistoryFirstEventAt"]
        require(projected == drawing_expected and observed["self_creation_equals_header"],
                "independent drawing clock domain changed")
        drawing_rows[label] = observed
    require("Contents/CMgrHdr2" not in drawing_archive.streams,
            "drawing clock experiment unexpectedly gained a separate manager-header owner")
    require(WriteHeadGraph(drawing_top, 19000) == drawing_archive.require("Header2"), "drawing Header2 byte identity differs")
    profile = check_display(loaded.GraphValue, child.ResolvedValue.RootsValue, header)
    shape = inspect_child(child.ResolvedValue.RootsValue, "corner-anchored")
    require(profile == result["profile"] and shape == result["child_shape"],
            "independent epoch preparation lost actual origin or neutral geometry ownership")
    return {"schema": "kit.sw2026.sdk-epoch-pair-preparation.v1", "passed": True, "case": request["case"],
            "child_sha256": result["child_sha256"], "drawing_sha256": result["drawing_sha256"],
            "child_model_header_clocks": child_clocks, "child_top_header_clocks": top_clocks,
            "child_model_header": observe_header(header, model), "child_history": hist,
            "drawing_headers": drawing_rows, "drawing_history": drawing_hist,
            "drawing_has_independent_manager_header": False,
            "child_exact_linked_streams": list(roundtrips), "child_history_byte_identity": True,
            "drawing_definition_header_history_byte_identity": True, "profile": profile, "child_shape": shape,
            "config_map_next": child.ConfigValue.MapValue.CounterValue,
            "resolved_map_next": child.ResolvedValue.MapValue.CounterValue,
            "native_acceptance": False, "heldout_acceptance": False, "public_drawing_writer_enabled": False}


if __name__ == "__main__":
    try:
        print(json.dumps(main(), sort_keys=True, ensure_ascii=False, allow_nan=False))
    except Exception as error:
        print(json.dumps({"passed": False, "exception": type(error).__name__, "diagnostic": str(error), "native_acceptance": False}))
        raise SystemExit(3)
