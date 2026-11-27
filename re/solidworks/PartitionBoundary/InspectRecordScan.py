from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from subprocess import check_output
import sys

REVISION = "c0a401a607759fb0c2589647c2a22af65ebb7ce1"
TOOLS_TREE = "4503ec0e1e833b443cf111886dff42941f0a1bc4"
CASES = {
    "four_line": "f5647d6c571760a7dd6dda228e2dea7b99bb6798c2bbe2b7bb1d5d2f006d800a",
    "five_line": "0cbf1cc45171ca8e3e1cc101cee45e81d71d95d2c25df355f67f265d1a8155ba",
    "vendor_control": "db1390476325f5817e6f80fb4067a3c6df5cc063315604c133ccbeaafdeac357",
}


def digest(raw):
    return sha256(raw).hexdigest()


def demand(value, reason):
    if not value:
        raise ValueError(reason)


def git(root, *args):
    return check_output(("git", "--no-optional-locks", "-C", str(root), *args))


def initialize(sdk, tools):
    demand(git(sdk, "rev-parse", "HEAD").decode().strip() == REVISION,
           "record diagnosis requires the exact PR121 dependency")
    demand(not git(sdk, "status", "--porcelain", "--untracked-files=no"), "SDK has tracked changes")
    demand(git(sdk, "rev-parse", "HEAD:re/tooling/sw2026").decode().strip() == TOOLS_TREE,
           "research tooling tree differs")
    sys.path[:0] = [str(sdk / "src"), str(tools), str(tools / "serial")]


def inspect(path, role):
    from convert import open_document
    from convert.Geometry.Parasolid import BuildPartModel, ParaHeaderData, ParseVertexUse, ReadBrepResult, ScanPartRecords, SolidFaceData
    from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
    from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
    from convert.adapters.solidworks.Archive.Partition.ReadXmtNodeMut import ReadXmtNodeMut
    from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Container.Parasolid import DecodePartition
    from para.Partition import frame_payloads, read_partition, write_payloads

    raw = path.read_bytes()
    demand(digest(raw) == CASES[role], "input differs from its disclosed exact role")
    receipt_raw, receipt = None, {}
    if role != "vendor_control":
        receipt_raw = path.with_name("Evidence.json").read_bytes()
        receipt = json.loads(receipt_raw)
        demand(receipt["attached_sha256"] == digest(raw), "origin receipt does not bind the input")
    archive = SldprtArchive.from_bytes(raw, role)
    member = archive.Require("Contents/Config-0-Partition")
    structural, structural_reason = False, ""
    try:
        physical_partition = read_partition(member)
        structural = frame_payloads(write_payloads(physical_partition)) == member
    except ValueError as failure:
        demand(role == "vendor_control", "generated structural partition replay refused")
        structural_reason = str(failure)
    demand(structural or role == "vendor_control", "structural partition replay differs")
    payload, = (item for item in DecodePartition(member) if item.kind == "partition")
    header = ParaHeaderData(payload.data)
    demand(header is not None and header.schema == "SCH_3701250_37102_13006", "transmit schema differs")
    body = payload.data[header.body_offset:]
    sdk_nodes = ReadActiveNodes(payload.data)
    CheckXmtGraph(sdk_nodes)
    pairs = sorted((node.IndexValue, node.Integer("point")) for node in sdk_nodes.values() if node.KindValue == 18)
    counts_by_role = {"four_line": (177, 8), "five_line": (203, 10), "vendor_control": (180, 8)}
    demand((len(sdk_nodes), len(pairs)) == counts_by_role[role]
           and all(sdk_nodes[target].KindValue == 29 for _, target in pairs), "existing SDK typed vertex ownership differs")
    before, reason = ReadBrepResult(payload.data)
    public = open_document(raw, source_format="solidworks.sldprt", strict=True)
    scanner = ScanPartRecords(body)
    demand(scanner is not None, "record scan exceeded its limits")
    cursor = XmtCursor(body)
    spans = {}
    while True:
        start = cursor.OffsetValue
        kind = cursor.ReadKind()
        if kind == 1:
            break
        node = ReadXmtNodeMut(cursor, kind)
        spans[node.IndexValue] = (start, cursor.OffsetValue, node)
    cursor.FinishRead()
    demand(set(sdk_nodes) == set(spans)
           and all(sdk_nodes[index] == node for index, (_, _, node) in spans.items()),
           "SDK typed record inventories differ")
    vertices = [(start, end, node, ParseVertexUse(body, start))
                for start, end, node in spans.values() if node.KindValue == 18]
    demand(all(value is not None for _, _, _, value in vertices), "typed vertex boundary was not recognized")
    collisions = []
    authoritative = {}
    for start, end, node, actual in vertices:
        demand(actual.attribute == node.IndexValue + 1 and actual.references[4] == node.Integer("point") + 1,
               "typed index and scanner attribute domains differ")
        demand(actual.attribute not in authoritative, "typed vertex ownership aliases")
        authoritative[actual.attribute] = actual
        chosen = scanner.vertex_uses[actual.attribute]
        if chosen.offset == start:
            continue
        owner_start, owner_end, owner = next(row for row in spans.values() if row[0] <= chosen.offset < row[1])
        point_start, point_end, point = spans[node.Integer("point")]
        collisions.append({"scanner_attribute": actual.attribute, "chosen_offset": chosen.offset,
                           "chosen_references": chosen.references, "chosen_point_exists": chosen.references[4] in scanner.points,
                           "containing_kind": owner.KindValue, "containing_index": owner.IndexValue,
                           "containing_span": [owner_start, owner_end], "true_vertex_index": node.IndexValue,
                           "true_vertex_span": [start, end], "true_references": actual.references,
                           "true_point_index": point.IndexValue, "true_point_span": [point_start, point_end],
                           "true_point_attribute": actual.references[4]})
        demand(owner.KindValue == 17 and owner.Integer("vertex") == node.IndexValue and point.KindValue == 29,
               "collision does not have the disclosed typed fin and point ownership")
    isolated = replace(scanner, vertex_uses=authoritative)
    model = BuildPartModel(isolated, *SolidFaceData(body))
    errors = model.validate()
    counts = [len(model.faces), len(model.edges), len(model.vertices)]
    demand(not errors and counts == ([7, 15, 10] if role == "five_line" else [6, 12, 8]),
           "diagnostic authoritative vertex reconstruction differs")
    diagnostic = {"topology": counts, "validation_errors": len(errors),
                  "vertex_map_entries": len(authoritative),
                  "scope": "all typed vertex entries in a local copied table; no SDK or input modification"}
    if role != "five_line":
        demand(before is not None and not reason and public.brep is not None and not collisions,
               "independent control no longer has its disclosed reader success")
    else:
        demand(before is None and public.brep is None
               and reason == "invalid partition topology (missing vertex point)" and len(collisions) == 1,
               "five line public refusal differs")
        item, = collisions
        demand(item["chosen_offset"] == 988 and item["containing_span"] == [978, 1001]
               and item["containing_index"] == 18 and item["true_vertex_span"][0] == 2809
               and item["true_point_span"][0] == 2837, "disclosed record boundaries differ")
        demand(scanner.vertex_uses[83].offset == 988 and ReadBrepResult(payload.data)[1] == reason,
               "diagnosis changed the public reader or original scanner table")
    demand(path.read_bytes() == raw and (receipt_raw is None or path.with_name("Evidence.json").read_bytes() == receipt_raw),
           "input custody changed during inspection")
    return {"archive_sha256": digest(raw), "origin_receipt_sha256": digest(receipt_raw) if receipt_raw else None,
            "partition_sha256": digest(member), "partition_bytes": len(member), "payload_sha256": digest(payload.data),
            "structural_exact_reemit": structural, "structural_refusal": structural_reason, "physical_record_count": len(spans),
            "sdk_read_active_nodes": {"complete_nodes": len(sdk_nodes), "checked_graph": True, "vertex_point_pairs": pairs},
            "public_returned": True, "public_body_count": len(public.bodies), "public_brep_returned": public.brep is not None,
            "public_diagnostics": sorted({item.code for item in public.diagnostics}),
            "payload_reader_brep_returned": before is not None, "payload_reader_reason": reason,
            "record_collisions": collisions, "diagnostic_only_reconstruction": diagnostic,
            "generation_base_sha256": receipt.get("base_sha256"),
            "generation_request_digests": {key: value for key, value in receipt.items() if key.endswith("request_sha256") or key == "presentation_input_sha256"}}


def provenance(sdk, tools):
    files = {}
    for module in tuple(sys.modules.values()):
        filename = getattr(module, "__file__", None)
        if not filename:
            continue
        path = Path(filename).resolve()
        if module.__name__.split(".", 1)[0] in ("convert", "interchange"):
            demand(path.is_relative_to(sdk / "src"), "SDK import escaped its pinned checkout")
        if path.is_relative_to(tools) and path.suffix == ".py":
            relative = "re/tooling/sw2026/" + path.relative_to(tools).as_posix()
            actual = path.read_bytes()
            expected = git(sdk, "show", REVISION + ":" + relative)
            demand(actual.replace(b"\r\n", b"\n") == expected.replace(b"\r\n", b"\n"), "typed tooling source differs")
            files[relative] = {"actual_sha256": digest(actual), "git_blob": git(sdk, "rev-parse", REVISION + ":" + relative).decode().strip()}
    demand(files, "typed record tooling was not imported")
    return {"research_tree": TOOLS_TREE, "tool_files": files,
            "sdk_parasolid_git_blob": git(sdk, "rev-parse", REVISION + ":src/convert/Geometry/Parasolid.py").decode().strip(),
            "sdk_active_nodes_git_blob": git(sdk, "rev-parse", REVISION + ":src/convert/adapters/solidworks/Archive/Partition/ReadActiveNodes.py").decode().strip()}


def main():
    parser = ArgumentParser(description="Compare exact typed partition record boundaries with the unchanged public scan")
    for name in ("sdk-root", "tools-root", "four-line", "five-line", "vendor-control", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    sdk, tools = args.sdk_root.resolve(), args.tools_root.resolve()
    initialize(sdk, tools)
    records = {role: inspect(path, role) for role, path in (("four_line", args.four_line), ("five_line", args.five_line), ("vendor_control", args.vendor_control))}
    report = {"schema": "kit.research.partition-record-scan.v1", "sdk_revision": REVISION,
              "method_sha256": digest(Path(__file__).read_bytes()), "provenance": provenance(sdk, tools),
              "cases": records, "input_mutation": False, "sdk_behavior_patch": False, "native_launches": 0,
              "acceptance": "offline diagnostic only; native and ordinary source acceptance unqualified"}
    demand(not git(sdk, "status", "--porcelain", "--untracked-files=no"), "SDK changed during diagnosis")
    wire = (json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode()
    with args.output.open("xb") as target:
        target.write(wire)
    print(digest(wire))


if __name__ == "__main__":
    main()
