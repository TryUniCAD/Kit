import json
import os
import sys

sys.dont_write_bytecode = True
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026"), str(ROOT / "re/tooling/sw2026/serial")]

from SdkPlanarMateProcess import AUDIT, AssemblyDocument, BuildSldprt, ReadMatesMut, ReadNativeLink, SldprtArchive, WriteMatesMut, digest, inspect_readback, registry, codecs
from SdkPlanarFaults import RejectedInput
from SdkDistanceBridge import DistanceBridge
from convert.adapters.solidworks.Archive.Construction.PlanarMates.FieldRecord import FieldRecord


def inspect_distance(link, graph, bundle):
    mate, = graph.RootsValue
    display = mate.FieldsValue["f4b8"]
    handle, = (row["o"] for row in display.FieldsValue["f850"])
    dimension = handle.FieldsValue["ff0"]
    parameter = dimension.FieldsValue["f28"]
    value = parameter.FieldsValue["f58"]
    spec, = bundle["mates"]
    if value != spec["distance_m"] or parameter.FieldsValue["f08"] != -1 or parameter.FieldsValue["f68"] != 0:
        raise ValueError("distance readback lost the live unassigned local parameter")
    if dimension.FieldsValue["f50"] >= mate.FieldsValue["f08"] or dimension.FieldsValue["refcount"] != 1 or handle.FieldsValue["fe8"] is not None or handle.FieldsValue["f100"] is not None:
        raise ValueError("distance readback lost dimension allocation or actual retaining handle")
    header = link.ConfigValue.HeaderValue
    logs = FieldRecord(header.FieldsValue["f20"])["items"]
    log_ids = [row.FieldsValue["f48"] for row in logs]
    if mate.FieldsValue["f08"] not in log_ids or dimension.FieldsValue["f50"] in log_ids:
        raise ValueError("distance dimension must not create a separate feature revision log")
    return {"value_metres": value, "parameter_name": parameter.FieldsValue["f18"].FieldsValue["f08"], "parameter_id": parameter.FieldsValue["f08"], "dimension_id": dimension.FieldsValue["f50"], "mate_id": mate.FieldsValue["f08"], "header_next_id": header.FieldsValue["f08"], "dimension_log_absent": True, "retaining_handle_count": dimension.FieldsValue["refcount"], "text_kind": display.FieldsValue["f6a0"]["f10"], "constructor_value_cache": display.FieldsValue["fad0"], "options": [mate.FieldsValue[key] for key in ("f3b4", "f4c0", "f4d8", "f4dc", "f4e0", "f4f4")]}


def main():
    request = json.load(sys.stdin)
    mode = request.get("mode", "sdk")
    bundle = request["bundle"]
    if mode not in ("sdk", "reference") or len(bundle.get("mates", [])) != 1 or bundle["mates"][0].get("kind") != "distance":
        raise ValueError("distance process requires one explicit ordinary distance mate")
    tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    rules = registry()
    bridge = DistanceBridge(AssemblyDocument, request.get("fault"))
    if mode == "sdk":
        bridge.install()
    rejection = None
    AUDIT.BeginBuild()
    try:
        result = AssemblyDocument.construct_assembly_bundle(registry=rules, request=bundle, include_xml_metadata=True)
        parent = BuildSldprt(result.assembly.streams, format_version=4)
        child = BuildSldprt(result.child.streams, format_version=4)
        archive = SldprtArchive.from_bytes(parent)
        link = ReadNativeLink(archive, 0)
        blob = archive.require("Contents/Config-0-MatesList")
        graph = ReadMatesMut(blob, link.ResolvedValue)
        encoded, stored = WriteMatesMut(graph.RootsValue, link.ResolvedValue)
        if encoded != blob:
            raise ValueError("complete SDK distance mate stream failed its actual map round trip")
        readback = inspect_readback(link, graph, bundle)
        readback["driving_distance"] = inspect_distance(link, graph, bundle)
    except RejectedInput:
        rejection = bridge.rejection
    finally:
        bridge.restore()
    if AUDIT.DeniedReads:
        raise ValueError("distance construction attempted runtime input access")
    if rejection is not None:
        print(json.dumps({"mode": mode, "passed": True, "worker_pid": os.getpid(), "rejected": True, "rejection": rejection, "writer_output_count": 0, "runtime_file_read_attempts": 0, "native_processes_started": 0}, sort_keys=True))
        return
    output = {"mode": mode, "passed": True, "worker_pid": os.getpid(), "writer_output_count": 2, "runtime_file_read_attempts": 0, "native_processes_started": 0, "public_writer_enabled": False, "native_acceptance": False, "assembly": {"sha256": digest(parent), "bytes": len(parent), "streams": {name: {"bytes": len(data), "sha256": digest(data)} for name, data in sorted(result.assembly.streams.items())}}, "child": {"sha256": digest(child), "bytes": len(child)}, "mate_stream": {"sha256": digest(blob), "bytes": len(blob), "map_base": graph.MapBase, "map_terminal": graph.MapValue.CounterValue, "read_coverage": dict(graph.ReportValue), "write_coverage": dict(stored.ReportValue)}, "readback": readback, "constructor": bridge.report}
    print(json.dumps(output, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
