import codecs
import hashlib
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026"), str(ROOT / "re/tooling/sw2026/serial")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

import builders.AssemblyDocument as AssemblyDocument
from Classes import registry
from SdkPlanarBridge import PlanarBridge
from SdkPlanarFaults import RejectedInput
from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
from convert.adapters.solidworks.Container.Container import SldprtArchive, BuildSldprt
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inspect_readback(link, graph, bundle):
    parent = link.ConfigValue.RootValue
    group, = (value for value in link.ResolvedValue.RootsValue if value.ClassValue.NameValue == "moMateGroup_c")
    mate, = graph.RootsValue
    if "owner" in mate.FieldsValue or "owner" in group.FieldsValue:
        raise ValueError("ordinary feature ownership must remain outside this wire projection")
    occurrences = [row["o"] for row in parent.FieldsValue["f68"]["list"]["items"]]
    wrappers = [row["o"] for row in mate.FieldsValue["f410"]]
    detached = [row["o"] for row in mate.FieldsValue["f3c8"]]
    ordinal_values = [value["occurrence"] for value in bundle["mates"][0]["endpoints"]]
    for wrapper, ordinal in zip(wrappers, ordinal_values, strict=True):
        reference = wrapper.FieldsValue["f58"]
        chain = reference.FieldsValue["f58"]
        external = chain.FieldsValue["f20"].FieldsValue["f08"].FieldsValue["f08"][0]["o"]
        occurrence = occurrences[ordinal]
        if chain.FieldsValue["owner"] is not parent or external is not occurrence.FieldsValue["f4f8"] or external.FieldsValue["f50"] is not occurrence:
            raise ValueError("constructed SDK mate lost an ordered actual occurrence backlink")
    components = [value.FieldsValue["f58"].FieldsValue["f58"] for value in detached]
    planes = [value.FieldsValue["f58"].FieldsValue["ff8"] for value in detached]
    if components[0] is components[1] or planes[0] is planes[1] or any(value.FieldsValue["owner"] is not parent for value in components):
        raise ValueError("constructed SDK mate lost independent detached owner aliases")
    return {"actual_component_parent_identity": True, "resolved_group_id": group.FieldsValue["f08"], "feature_owner_is_loader_attachment": True, "actual_ordered_occurrence_backlinks": True, "exclusive_detached_components": True, "independent_unregistered_planes": [value.FieldsValue["f08"] for value in planes], "mate_id": mate.FieldsValue["f08"], "ordered_occurrence_ids": [occurrences[value].FieldsValue["f08"] for value in ordinal_values], "ordered_datum_ids": [value.FieldsValue["f58"].FieldsValue["ff0"]["f00"] for value in wrappers]}


def main():
    request = json.load(sys.stdin)
    mode = request.get("mode", "sdk")
    if mode not in ("sdk", "reference"):
        raise ValueError("choose SDK or reference composer")
    bundle = request["bundle"]
    if len(bundle.get("mates", [])) != 1 or bundle["mates"][0].get("kind") not in ("coincident", "parallel"):
        raise ValueError("SDK construction process requires one authored coincident or parallel mate")
    tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    rules = registry()
    bridge = PlanarBridge(AssemblyDocument, request.get("fault"))
    if mode == "sdk":
        bridge.install()
    AUDIT.BeginBuild()
    rejection = None
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
            raise ValueError("constructed mate stream failed its real SDK round trip")
        readback = inspect_readback(link, graph, bundle)
    except RejectedInput:
        rejection = bridge.rejection
    finally:
        bridge.restore()
    if AUDIT.DeniedReads:
        raise ValueError(f"fresh SDK mate construction attempted a runtime file read: {AUDIT.DeniedReads!r}")
    if rejection is not None:
        print(json.dumps({"mode": mode, "passed": True, "worker_pid": os.getpid(), "rejected": True, "rejection": rejection, "writer_output_count": 0, "runtime_file_read_attempts": 0, "native_processes_started": 0}, sort_keys=True))
        return
    output = {"mode": mode, "passed": True, "worker_pid": os.getpid(), "writer_output_count": 2, "runtime_file_read_attempts": len(AUDIT.DeniedReads), "native_processes_started": 0, "public_writer_enabled": False, "native_acceptance": False, "assembly": {"sha256": digest(parent), "bytes": len(parent), "streams": {name: {"bytes": len(data), "sha256": digest(data)} for name, data in sorted(result.assembly.streams.items())}}, "child": {"sha256": digest(child), "bytes": len(child)}, "mate_stream": {"sha256": digest(blob), "bytes": len(blob), "map_base": graph.MapBase, "map_terminal": graph.MapValue.CounterValue, "read_coverage": dict(graph.ReportValue), "write_coverage": dict(stored.ReportValue)}, "readback": readback, "constructor": bridge.report}
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
