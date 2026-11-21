from argparse import ArgumentParser
from pathlib import Path
from subprocess import run
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent)]

from AuditPatternDatumPlacement import ANGLE_PLANE, replay
from AuditPatternEnvelope import SldprtArchive
from PatternHingeWire import read_axis_stream, write_roots
from ProvePatternPlaneDirectionRule import checked, digest, document_rows, encode, require
from tests.Convert.Solidworks.Research.Construction.Part.MakePolygonCase import MakePolygonCase
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Counts.ReadCount import ReadCount
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName, RequireNode


def disclosed_source(path, sha):
    raw = checked(path, sha)
    archive = SldprtArchive.from_bytes(raw)
    header = ReadHeaderGraph(archive.require("Contents/Config-0-ModelHeader"), 19000)
    config = ReadConfigMut(archive.require("Contents/Config-0"), 19000, header)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000)
    scope = MakeLinkContext(config, manager)
    resolved = archive.require("Contents/Config-0-ResolvedFeatures")
    roots, read_map, end = read_axis_stream(resolved, config.MapValue, scope, disclosed_prefix=True)
    stream, write_map = write_roots(roots, config.MapValue, scope, disclosed_prefix=True)
    actual_count, native_prefix = ReadCount(resolved, 4)
    replay_count, generated_prefix = ReadCount(stream, 4)
    require(len(roots) == replay_count and actual_count > replay_count and stream[:4] == resolved[:4]
            and stream[generated_prefix:] == resolved[native_prefix:end] and read_map == write_map,
            "actual disclosed ordered axis root prefix refuses exact replay")
    axis = RequireNode(roots[-1], "moRefAxis_c")
    data = RequireNode(axis.FieldsValue["f700"], "moPlaneInterAxisData_c").FieldsValue
    owners = []
    for field, expected in (("f80", "Top Plane"), ("f88", "Right Plane")):
        view = RequireNode(data[field], "moPlaneRef_w").FieldsValue
        selection = RequireNode(view["f58"], "moCompRefPlane_c").FieldsValue
        component = RequireNode(selection["f58"], "moUnitComponent_c")
        key = selection["ff0"]["f00"]
        (datum,) = [node for node in roots if node is not None and node.FieldsValue.get("f08") == key]
        require(ReadNodeName(datum) == expected and component.FieldsValue["owner"] is config.RootValue
                and selection["ff0"]["f08"] == DatumTime(header, key), "disclosed prefix lost the actual ordered plane target")
        owners.append(component)
    require(owners[0] is not owners[1], "disclosed selected unit components alias")
    _, full, _ = replay(raw)
    next_root = full[replay_count]
    require(next_root.cls == "moRefPlane_c" and next_root["f6f8"].cls == ANGLE_PLANE,
            "the first unrepresented source owner is a different datum")
    return {"sha256": sha, "native_root_count": actual_count, "compared_prefix_root_count": replay_count,
            "resolved_prefix_end_exclusive": end, "linked_prefix_map": [config.MapValue.CounterValue, write_map.CounterValue],
            "axis_id": axis.FieldsValue["f08"], "next_complex_body": next_root["f6f8"].cls}


def generated_model(label, width, height, bigger):
    vertices = ((0.0, 0.0), (width, 0.0), (width, height), (0.0, height))
    document = MakePolygonCase(label, vertices, bigger)["document"]
    request = {"document": document, "path": f"C:\\KitFiniteHingeModel\\{label}.SLDPRT", "axis_name": label + " finite axis",
               "epoch": 1795092001}
    raw = encode(request)
    command = (sys.executable, "-I", "-B", str(HERE.with_name("ProvePatternHingeAxis.py")))
    results = [run(command, input=raw, capture_output=True, cwd=ROOT, check=True, timeout=30) for _ in range(2)]
    first, second = results
    require(not first.stderr and not second.stderr and first.stdout == second.stdout, "model-derived finite axis output differs by process")
    model = json.loads(first.stdout)
    require(model["completed_model_fragment"] and model["guarded_runtime_reads"] == 0
            and not model["native_acceptance"] and not model["container_written"] and len(model["refusals"]) == 2,
            "finite axis output is outside its guarded research profile")
    return {"neutral_request_sha256": digest(raw), **model}


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosed-share", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = {path.name: disclosed_source(path, sha) for path, sha, row in document_rows(args.disclosed_share)
            if row["plane_data_class"] == ANGLE_PLANE}
    models = {name: generated_model(name, width, height, bigger) for name, width, height, bigger in (
        ("HingeAlpha", 157.375, 94.625, True), ("HingeBeta", 113.625, 81.125, False),
    )}
    first, second = models.values()
    require(len(rows) == 4 and first["axis"]["start_m"] != second["axis"]["start_m"]
            and first["resolved_sha256"] != second["resolved_sha256"], "need four actual sources and a real model contrast")
    result = {"schema": "kit.sw2026.finite-hinge-research-graph.v1", "generative_cases": models,
              "disclosed_prefix_replays": rows, "separate_guarded_processes": 4, "native_calls": 0, "heldout_inputs_read": 0,
              "tool_sha256": {name: digest(HERE.with_name(name).read_bytes()) for name in (
                  "MakePatternHingeAxis.py", "PatternHingeWire.py", "ProvePatternHingeAxis.py", HERE.name)}}
    with args.output.open("xb") as file:
        file.write(encode(result))
    print(digest(args.output.read_bytes()))


if __name__ == "__main__":
    main()
