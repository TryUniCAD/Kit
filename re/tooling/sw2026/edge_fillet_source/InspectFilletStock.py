from argparse import ArgumentParser
from json import dumps, loads
from math import dist, isfinite
from pathlib import Path
from re import fullmatch
from subprocess import check_output, run
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(HERE.parent)]

from FilletModel import require
from FilletPacket import CONTROL, job_bytes
from FilletStockPacket import NAMES, ORACLE_AUTHORITY, PHASES, REGISTERED_API, load_job, pinned, sha, write_new
from ProveFilletInputs import guard
from RunFilletStock import BOSS, SCHEMA, SKETCH

from convert.Geometry.Parasolid import DecodePartData
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Partition.CheckXmtAttrs import CheckXmtAttrs
from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.CheckBodyTags import CheckBodyTags
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import ReadBodyAttrs
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyOwner import ReadBodyOwner
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyTree import ReadBodyTree
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadMgrAtom import ReadMgrAtom
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadOutputAtom import ReadOutputAtom
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.Warm.PickWarmEdge import ReadWarmPick, ReadWarmPoint
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.ReadFilletFace import ReadFilletFace
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName

KERNEL = "SCH_3701250_37102_13006"
COUNTS = {"faces": 6, "edges": 12, "vertices": 8}
EDGE_TOL = 1e-9


def points_equal(left, right):
    return len(left) == len(right) and all(
        sum(dist(a, b) <= EDGE_TOL for b in right) == 1 for a in left
    ) and all(sum(dist(a, b) <= EDGE_TOL for a in left) == 1 for b in right)


def good_points(points, count):
    return isinstance(points, list) and len(points) == count and all(
        isinstance(row, list) and len(row) == 3 and all(type(value) is float and isfinite(value) for value in row)
        for row in points
    )


def inspect_stock(raw, edge_points, vertices):
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    require(all(report.get("completed") and not report.get("missing_schemas") and not report.get("provisional_schemas")
                for report in (link.ConfigValue.ReportValue, link.ResolvedValue.ReportValue)),
            "stock requires complete typed Config-0 and ResolvedFeatures")
    boss = ReadBodyOwner(link, None)
    roots = link.ResolvedValue.RootsValue
    profiles = tuple(value for value in roots if value is not None and value.ClassValue.NameValue == "moProfileFeature_c")
    require(ReadNativeName(boss) == BOSS and len(profiles) == 1 and ReadNativeName(profiles[0]) == SKETCH
            and not any(value is not None and value.ClassValue.NameValue == "Fillet_c" for value in roots),
            "archive does not bind the qualified stock-only sketch and boss")
    producer = NativeNodeId(boss)
    atom = ReadMgrAtom(link)
    require(ReadOutputAtom(boss) is atom, "stock boss output does not own the actual configuration atom")
    require(KPartitionStream in archive.streams, "saved stock has no native active partition")
    stream = archive.require(KPartitionStream)
    payloads = DecodePartData(stream, KPartitionStream)
    require(tuple(item.kind for item in payloads) == ("partition", "deltas")
            and all(item.schema == KERNEL for item in payloads), "saved stock uses an alternate partition grammar")
    nodes = ReadActiveNodes(payloads[0].data)
    CheckXmtGraph(nodes)
    tree = ReadBodyTree(nodes)
    body = nodes[tree.BodyIndex]
    CheckXmtAttrs(nodes, body)
    CheckBodyTags(atom, producer, nodes, ReadBodyAttrs(nodes, body))
    expected_vertices = tuple(ReadWarmPoint(nodes, slot) for slot in tree.VertexIds)
    require(points_equal(expected_vertices, vertices), "saved stock vertices differ from the native probe")
    header = ReadHeaderGraph(archive.require("Header2"), 19000)
    epoch = DatumTime(header, producer)
    roles = {slot: ReadFilletFace(nodes, slot, producer, epoch) for slot in tree.FaceIds}
    require(set(roles.values()) == ({("moFromSktEntSurfIdRep_c", ordinal, None) for ordinal in range(1, 5)}
                                    | {("moEndFaceSurfIdRep_c", ordinal, 0) for ordinal in range(2)}),
            "stock face roles do not cover its four actual sides and two ends")
    matches = []
    for edge in tree.EdgeIds:
        fins, faces = ReadWarmPick(nodes, edge)
        endpoints = tuple(ReadWarmPoint(nodes, fin.Integer("vertex")) for fin in fins[::-1])
        if points_equal(endpoints, edge_points):
            matches.append((edge, fins, faces, endpoints))
    require(len(matches) == 1, "native observation does not select a unique physical stock edge")
    edge, fins, faces, endpoints = matches[0]
    require(len(set(faces)) == 4, "physical stock selection has non-distinct face roles")
    return {"archive_sha256": sha(raw), "partition_sha256": sha(stream), "active_sha256": payloads[0].sha256,
            "body_slot": tree.BodyIndex, "atom_id": atom.FieldsValue["f140"], "creator_id": producer,
            "creator_epoch": epoch, "edge_slot": edge, "edge_node_id": nodes[edge].Integer("node_id"),
            "positive_fin_slot": fins[0].IndexValue, "positive_fin_endpoints_m": endpoints,
            "face_slots": faces, "ordered_roles": [roles[slot] for slot in faces]}


def worker():
    packet = loads(sys.stdin.buffer.read())
    data = bytes.fromhex(packet["bytes_hex"])
    checks = guard()
    try:
        result = inspect_stock(data, packet["edge_endpoints_m"], packet["body_vertices_m"])
    except (KeyError, ValueError) as error:
        result = {"archive_sha256": sha(data), "refused": str(error)}
    require(not checks, "typed stock inspection accessed an external input")
    print(dumps(result | {"guarded_external_accesses": len(checks)}, sort_keys=True, allow_nan=False))


def native_phases(job, job_pin, result_path, result_pin):
    result = loads(pinned(result_path.absolute(), result_pin))
    require(result["schema"] == SCHEMA and result["stock_job_sha256"] == job_pin and result["oracle"] == ORACLE_AUTHORITY
            and result["passed"] is True and result["comparison_valid"] is True and result["oracle_idle_after"] is True
            and result["fillet_writer_output_count"] == result["heldout_sources_read"] == 0
            and result["candidate_unchanged_after_bracket"] == dict.fromkeys(NAMES, True), "native stock bracket did not pass")
    phases = result["phases"]
    require(set(phases) == set(PHASES) and result["distinct_native_processes"] == 4
            and len({tuple(item["process"]) for item in phases.values()}) == 4
            and all(item["passed"] is True and item["executable_sha256"] == ORACLE_AUTHORITY["sha256"]
                    and item["executable_build"] == ORACLE_AUTHORITY["build"] and not item["worker_timed_out"]
                    and not item["dialogs_observed"] and not item["cleanup_diagnostics"]
                    and fullmatch(r"[a-f0-9]{64}", item["raw_receipt_sha256"])
                    for item in phases.values()), "native stock phase provenance differs")
    require(all(phases[name]["control_sha256"] == CONTROL for name in ("ControlBefore", "ControlAfter")),
            "native stock bracket has an alternate control")
    for name in NAMES:
        row = phases[name]
        require(row["candidate_sha256"] == job["construction"][name]["sha256"] and row["candidate_unchanged"] is True
                and row["registered_api_sha256"] == REGISTERED_API
                and row["open_status"] == {"opened": True, "errors": 0, "warnings": 0}
                and row["cold_counts"] == row["rebuilt_counts"] == COUNTS
                and row["numeric_checks"] == row["numeric_passed"] > 0
                and fullmatch(r"[a-f0-9]{64}", row["native_save_sha256"])
                and good_points(row["edge_endpoints_m"], 2) and good_points(row["body_vertices_m"], 8),
                f"native physical stock measurements differ: {name}")
    return phases


def supervise(args):
    job, _, _, _ = load_job(args.job, args.job_sha256)
    sdk = check_output(("git", "rev-parse", "HEAD:src"), cwd=ROOT).decode().strip()
    require(sdk == job["sdk_tree"] and not check_output(("git", "status", "--porcelain", "--", "src"), cwd=ROOT),
            "physical fin inspection requires the exact SDK tree used for construction")
    phases = native_phases(job, args.job_sha256, args.result, args.result_sha256)
    folder = args.native_saved.absolute()
    require(folder.is_dir() and folder.resolve() == folder and {path.name for path in folder.iterdir()}
            == {f"{name}.SLDPRT" for name in NAMES}, "expected only the two immutable native save derivatives")
    found = {}
    for name in NAMES:
        row = phases[name]
        raw = pinned(folder / f"{name}.SLDPRT", row["native_save_sha256"])
        request = {"bytes_hex": raw.hex(), "edge_endpoints_m": row["edge_endpoints_m"], "body_vertices_m": row["body_vertices_m"]}
        child = run((sys.executable, "-I", "-B", str(HERE), "--worker"), cwd=ROOT, input=job_bytes(request),
                    capture_output=True, timeout=60, check=False)
        require(child.returncode == 0 and not child.stderr, child.stderr.decode(errors="replace"))
        found[name] = loads(child.stdout)
        require(found[name]["archive_sha256"] == row["native_save_sha256"], "saved stock changed in transport")
    passed = all("refused" not in row for row in found.values())
    receipt = {"schema": "kit.sw2026.edge-fillet-stock-fin.v1", "stock_job_sha256": args.job_sha256,
               "native_result_sha256": args.result_sha256, "sdk_tree": sdk, "physical_fins": found,
               "new_native_processes": 0, "fillet_writer_output_count": 0, "passed": passed}
    raw = job_bytes(receipt)
    write_new(args.report, raw)
    print(dumps({"passed": passed, "report_sha256": sha(raw)}, sort_keys=True))
    return passed


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--job", type=Path)
    parser.add_argument("--job-sha256")
    parser.add_argument("--result", type=Path)
    parser.add_argument("--result-sha256")
    parser.add_argument("--native-saved", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.worker:
        worker()
        return 0
    require(all((args.job, args.job_sha256, args.result, args.result_sha256, args.native_saved, args.report)),
            "supply the exact packet, native result, derivative directory and fresh report path")
    return 0 if supervise(args) else 2


if __name__ == "__main__":
    raise SystemExit(main())
