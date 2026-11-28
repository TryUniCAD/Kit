from argparse import ArgumentParser
from base64 import b64decode, b64encode
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
from subprocess import run
import sys
from uuid import UUID

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
TOOLS = ROOT / "re/tooling/sw2026"
CORPUS = ROOT / "re/solidworks/v2026/corpus"
sys.path[:0] = [str(HERE.parent), str(ROOT / "src"), str(ROOT), str(TOOLS), str(ROOT / "re/solidworks/WriterResearch")]

from AssemblyModelExchange import MATE_STREAM, add_model_exchange, model_records
from ConfigHeaderExchangeModel import MODEL_EXCHANGE_STREAM
from ExchangeMessagePack import read_exchange_map
from ExchangeMateEndpoints import project_exchange_target
from NativePlanarExchange import native_planar_exchange
from PlanarExchange import project_planar_exchange
from ProveD01ConcentricBridge import proof_guard, require
from ProveD01ModelExchange import next_ids, observed_ids

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadDatumFrame import ReadDatumFrame
from convert.adapters.solidworks.Archive.Exchange.ReadUnqlite import ReadUnqlite
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadChildStamp, ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.TypedMates.Cold.ReadMateDim import ReadMateDim
from convert.adapters.solidworks.Core.TypedMates.ReadMateChild import ReadMateBytes
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


BASE = "d89dd5965880fda9b645336527b20fc02557d4e9"
SOURCES = {
    "assemblies/A1_two.SLDASM": "594559a38ea2a077850a823e808ed7f79c559bfac743eab7c9ab4aa75cf252e4",
    "assemblies/A0_one.SLDASM": "66965b66e14bacb506b147fa354e6708aa207c7589efbf8e5f3d3fbe7cf453f8",
    "assembly-synchronized/A12SyncedEmpty.SLDASM": "b7d6e406c87dcfd6f4d6cc49c4c1723268afa77af205e017e10bd3039bbb10e2",
}
A1_MATES = (
    ("Coincident1", "moMateCoincident", 26, "3"),
    ("Distance1", "moMateDistanceDim_c", 28, "4"),
    ("Coincident2", "moMateCoincident", 29, "2"),
)


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(data):
    return sha256(data).hexdigest()


def checked(data, expected):
    require(digest(data) == expected, "input digest changed")
    return data


def linked(archive):
    link = ReadNativeLink(archive, 0)
    resolved = link.ResolvedValue
    physical = archive.require(MATE_STREAM)
    mates = ReadMatesMut(physical, resolved)
    replay, written = WriteMatesMut(mates.RootsValue, resolved)
    require(replay == physical
            and written.MapBase == mates.MapBase == resolved.MapValue.CounterValue
            and written.MapValue.CounterValue == mates.MapValue.CounterValue,
            "typed mate stream bytes or inherited map changed")
    header = ReadHeaderGraph(archive.require("Header2"), 19000)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000).RootValue
    owners = (link.ConfigValue.RootValue, header, manager, resolved.RootsValue, mates.RootsValue)
    return link, mates, owners


def mate_fields(payload):
    group = read_exchange_map(payload)
    count, = group.values("NumberMates") or (0,)
    rows = []
    for index in range(count):
        mate = group.field(f"Mate{index}")
        refs = tuple(mate.field(f"Ref{slot}") for slot in range(mate.field("NumberEntities")))
        require(all(ref.field("class") == "moPlaneRef_w"
                    and ref.field("dummy").field("class") == "moCompRefPlane_c" for ref in refs),
                "a projected endpoint lost its native wrapper and dummy maps")
        rows.append({
            "name": mate.field("description"),
            "class": mate.field("class"),
            "id": mate.field("id"),
            "entities": mate.field("NumberEntities"),
            "alignment": mate.field("Aligment"),
            "stamp": mate.field("updatestamp"),
            "hidden": mate.field("hidden"),
            "suppressed": mate.field("suppressed"),
            "distance_m": next(iter(mate.values("Distance")), None),
            "flip": next(iter(mate.values("FlipDim")), None),
            "feature_ids": [item.field("dummy").field("featureID") for item in refs],
            "targets": [item.field("dummy").field("target") for item in refs],
        })
    require([key for key, _ in group.pairs if key.startswith("Mate")] == [f"Mate{index}" for index in range(count)],
            "the parsed group has an unaccounted member")
    return rows


def refuses(action, expected):
    try:
        action()
    except ValueError as error:
        require(expected in str(error), "unexpected guarded refusal: " + str(error))
        return str(error)
    raise ValueError("unexpected projection of " + expected)


def rejects_field(fields, key, replacement, action, expected):
    original = fields[key]
    fields[key] = replacement
    try:
        return refuses(action, expected)
    finally:
        fields[key] = original


def source_refusals(link, mates):
    coincident, distance, _ = mates
    first, second = (row["o"] for row in distance.FieldsValue["f410"])
    component = first.FieldsValue["f58"]
    handle, = (row["o"] for row in distance.FieldsValue["f4b8"].FieldsValue["f850"])
    dimension = handle.FieldsValue["ff0"]
    first_ref = project_exchange_target(link.ConfigValue.RootValue, component)[0]

    def project():
        return project_planar_exchange(link, mates)

    parallel = ArchiveNode(RuntimeClass("moMateParallel", 1), coincident.FieldsValue)
    return {
        "unsupported_parallel_cell": refuses(lambda: project_planar_exchange(link, (parallel, *mates[1:])), "ordinary coincident and distance"),
        "misaligned_mode": rejects_field(distance.FieldsValue, "f3b4", 2, project, "alignment"),
        "unsupported_flip_mode": rejects_field(distance.FieldsValue, "f4c0", 0, project, "distance mate mode"),
        "negative_world_separation": rejects_field(second.FieldsValue, "fd0", {"x": -0.06, "y": 0.0, "z": -0.005}, project, "positive signed separation"),
        "non_aligned_world_normal": rejects_field(second.FieldsValue, "fe8", {"x": -1.0, "y": 0.0, "z": 0.0}, project, "aligned unit world planes"),
        "missing_live_parameter": rejects_field(dimension.FieldsValue, "f28", None, project, "moLengthParameter_c"),
        "detached_datum": rejects_field(component.FieldsValue["ff0"], "f00", -1, project, "live selected principal feature"),
        "stale_occurrence_update": rejects_field(first_ref.FieldsValue, "f3e0", 0, project, "occurrence update differs"),
        "wrong_wrapper_owner": rejects_field(first.FieldsValue, "f74", 0, project, "inconsistent ownership"),
        "reordered_reference_pair": rejects_field(distance.FieldsValue, "f410", tuple(reversed(distance.FieldsValue["f410"])), project, "inconsistent ownership"),
        "missing_occurrence_backlink": rejects_field(first_ref.FieldsValue, "f4f8", None, project, "lost its occurrence identity"),
    }


def distance_evidence(link, mates, projected):
    distance, = (mate for mate in mates if mate.ClassValue.NameValue == "moMateDistanceDim_c")
    display = distance.FieldsValue["f4b8"].FieldsValue
    dimension = ReadMateDim(distance)
    parameter = dimension.FieldsValue["f28"]
    cache = display["fad0"]
    display["fad0"] = 0.1234567
    try:
        require(project_planar_exchange(link, mates) == projected, "display cache falsely drove the exchange length")
    finally:
        display["fad0"] = cache
    return {"driver_name": ReadNodeName(parameter), "driver_id": dimension.FieldsValue["f50"],
            "length_span": [parameter.StartOffset, parameter.EndOffset],
            "length_m": parameter.FieldsValue["f58"], "display_cache_m": cache,
            "changed_cache_kept_exchange_exact": True}


def source_case(raw, expected, is_populated):
    archive = SldprtArchive.from_bytes(checked(raw, expected))
    link, graph, owners = linked(archive)
    store = archive.require(MODEL_EXCHANGE_STREAM)
    native_records = ReadUnqlite(store).Records
    ids = observed_ids(native_records)
    projected = project_planar_exchange(link, graph.RootsValue)
    generated = model_records(owners, ids, projected)
    require(len(generated) == 8 and generated == native_records,
            "complete native live model exchange records differ")
    payload = dict(generated)[str(ids.mates).encode("ascii")]
    fields = mate_fields(payload)
    if is_populated:
        require(tuple((row["name"], row["class"], row["id"], row["feature_ids"][0]) for row in fields) == A1_MATES
                and all(row["feature_ids"] == [feature, feature]
                        and row["alignment"] == 1 and row["stamp"] == 101
                        and row["entities"] == 2 and not (row["hidden"] or row["suppressed"])
                        and row["targets"] == ["L1_boss-1@Assem1", "P0_plain-1@Assem1"]
                        for row, (_, _, _, feature) in zip(fields, A1_MATES, strict=True))
                and [row["distance_m"] for row in fields] == [None, 0.06, None]
                and [row["flip"] for row in fields] == [None, 0, None]
                and type(fields[1]["flip"]) is int,
                "A1 typed member observations changed")
        rejected = source_refusals(link, graph.RootsValue)
        driver = distance_evidence(link, graph.RootsValue, projected)
        require(project_planar_exchange(link, graph.RootsValue) == projected, "refusals changed immutable observation")
    else:
        require(not fields, "empty native control gained a mate")
        rejected = {}
        driver = None
    return {
        "archive_sha256": expected, "store_sha256": digest(store), "live_records_matched": len(generated),
        "group_bytes": len(payload), "group_sha256": digest(payload), "mates": fields,
        "mates_list_bytes": len(archive.require(MATE_STREAM)), "mates_list_sha256": digest(archive.require(MATE_STREAM)),
        "mate_map": [graph.MapBase, graph.MapValue.CounterValue], "refusals": rejected, "driver": driver,
    }


def selected_child_endpoints(request, root, mates, child, active):
    config_id = active.FieldsValue["f08"]
    config_name = ReadNodeName(active)
    evidence = []
    for mate, authored in zip(mates, request["mates"], strict=True):
        for reference, expected in zip(mate.FieldsValue["f410"], authored["endpoints"], strict=True):
            wrapper = reference["o"]
            component = wrapper.FieldsValue["f58"]
            occurrence, target = project_exchange_target(root, component)
            name = request["occurrences"][expected["occurrence"]]["name"]
            file_text = ReadFileKey(occurrence.FieldsValue["f3b0"])[1]
            child_name = PureWindowsPath(request["child"]["settings"]["output"]["path_name"]).name.casefold()
            feature = component.FieldsValue["ff0"]["f00"]
            datum = child.DatumNodes.get(feature)
            require(datum is not None, "generated mate lost the selected actual child datum")
            _, axis = ReadDatumFrame(datum)
            stamp = ReadChildStamp(wrapper, occurrence, child, config_id, config_name, child_name)
            require(target == f"{name}@{request['assembly']['name']}"
                    and file_text == request["child"]["settings"]["output"]["path_name"]
                    and axis == "xyz".index(expected["axis"]) + 1
                    and component.FieldsValue["f100"] == axis,
                    "generated planar endpoint differs from its authored occurrence or datum")
            evidence.append({"target": target, "feature_id": str(feature), "axis": expected["axis"], "stamp": stamp})
    return evidence


def generated_case(j):
    request = j["request"]
    raw = checked(b64decode(j["assembly"]["blob"], validate=True), j["assembly"]["sha256"])
    child_bytes = checked(b64decode(j["child"]["blob"], validate=True), j["child"]["sha256"])
    archive = SldprtArchive.from_bytes(raw)
    link, graph, owners = linked(archive)
    child = ReadMateBytes(child_bytes, j["child"]["sha256"])
    child_archive = SldprtArchive.from_bytes(child_bytes)
    child_manager = ReadCmgrMut(child_archive.require("Contents/CMgr"), 19000).RootValue
    active = child_manager.FieldsValue["f360"]
    ends = selected_child_endpoints(request, owners[0], graph.RootsValue, child, active)
    selected = graph.RootsValue[0].FieldsValue["f410"][0]["o"].FieldsValue["f58"].FieldsValue["ff0"]
    foreign_datum = next(identity for identity in child.DatumNodes if identity != selected["f00"])
    wrong_datum = rejects_field(
        selected, "f00", foreign_datum,
        lambda: selected_child_endpoints(request, owners[0], graph.RootsValue, child, active),
        "differs from its authored occurrence or datum",
    )
    clock = datetime.fromtimestamp(request["assembly"]["output"]["saved_at"], UTC).replace(tzinfo=None)
    ids = next_ids(request, clock, UUID(int=0))
    projected = project_planar_exchange(link, graph.RootsValue)
    result = add_model_exchange(archive.streams, owners, ids, clock, projected)
    emitted = BuildSldprt(result, FormatVersion=4)
    after = SldprtArchive.from_bytes(emitted)
    require(after.streams == result and set(after.streams) - set(archive.streams) == {MODEL_EXCHANGE_STREAM}
            and all(after.require(key) == value for key, value in archive.streams.items()),
            "adding modeled exchange changed existing logical streams")
    store = after.require(MODEL_EXCHANGE_STREAM)
    records = ReadUnqlite(store).Records
    require(records == model_records(owners, ids, projected) and len(records) == 8,
            "generated exchange live records did not read back")
    fields = mate_fields(dict(records)[str(ids.mates).encode("ascii")])
    for index, (actual, authored) in enumerate(zip(fields, request["mates"], strict=True)):
        require(actual["name"] == authored["name"] and actual["entities"] == 2 and actual["alignment"] == 1
                and actual["distance_m"] == authored.get("distance_m")
                and actual["flip"] == (0 if authored["kind"] == "distance" else None)
                and actual["feature_ids"] == [row["feature_id"] for row in ends[2 * index:2 * index + 2]]
                and actual["targets"] == [row["target"] for row in ends[2 * index:2 * index + 2]],
                "new exchange map no longer represents the authored neutral mate")
    duplicate = refuses(lambda: add_model_exchange(result, owners, ids, clock, projected), "already has an owner")
    return {
        "neutral_request_sha256": digest(wire(request)), "assembly_input_sha256": digest(raw),
        "child_sha256": digest(child_bytes), "assembly_with_exchange_sha256": digest(emitted),
        "exchange_sha256": digest(store), "unchanged_logical_streams": len(archive.streams),
        "complete_exchange_records": len(records), "mates": fields, "live_child_endpoints": ends,
        "driver": distance_evidence(link, graph.RootsValue, projected),
        "refusals": {"different_live_child_datum": wrong_datum, "duplicate_exchange_owner": duplicate},
    }


def worker():
    request = json.load(sys.stdin)
    guard = proof_guard()
    if request["case"] == "generated":
        observed = generated_case(request)
    else:
        observed = source_case(b64decode(request["blob"], validate=True), request["sha256"], request["case"] == "A1")
    require(not guard, "an observation accessed external data or runtime")
    sys.stdout.buffer.write(wire(observed | {"external_access_attempts": len(guard)}))


def fresh(script, request, *args):
    argv = (sys.executable, "-I", "-B", str(script), *args)
    result = run(argv, input=wire(request), capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(f"guarded {script.name} exited {result.returncode}: " + result.stderr.decode("utf-8", "replace"))
    return json.loads(result.stdout)


def neutral_request(variant):
    from tests.Convert.Solidworks.Research.Construction.PlanarGroups.GroupCaseInput import GroupCaseInput

    request = GroupCaseInput(2, variant)
    first, second = request["occurrences"]
    gap = 0.09817 if variant else 0.04357
    second["origin"] = [x + gap * axis for x, axis in zip(first["origin"], first["u"], strict=True)]
    request["mates"][1].update(distance_m=gap, name="SpacingBeta" if variant else "SpacingAlpha")
    request["mates"][2].update(kind="coincident", name="LevelBeta" if variant else "LevelAlpha")
    return request


def model_cases():
    result = {}
    for variant in (False, True):
        request = neutral_request(variant)
        first, second = (fresh(TOOLS / "SdkPlanarGroupProcess.py", request, str(ROOT)) for _ in range(2))
        pids = (first.pop("worker_pid"), second.pop("worker_pid"))
        require(first == second and pids[0] != pids[1] and first["passed"] and first["round_trips"] == 22
                and first["runtime_input_file_reads"] == first["sdk_runtime_research_imports"] == 0,
                "independent neutral builds differ or touch external inputs")
        proof_request = {"case": "generated", "request": request, "assembly": first["assembly"], "child": first["child"]}
        one, two = (fresh(HERE, proof_request, "--worker") for _ in range(2))
        require(one == two, "guarded modeled exchange differs across fresh processes")
        result[request["assembly"]["name"]] = one | {"typed_archive_roundtrips_per_build": first["round_trips"]}
    return result


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--model-module", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        worker()
        return
    if args.model_module is None or args.output is None:
        parser.error("--model-module and --output required")
    native = native_planar_exchange(args.model_module)
    generated = model_cases()
    sources = {}
    for name, expected in SOURCES.items():
        source = checked((CORPUS / name).read_bytes(), expected)
        sources[name] = fresh(HERE, {
            "case": "A1" if name == "assemblies/A1_two.SLDASM" else "empty",
            "blob": b64encode(source).decode("ascii"), "sha256": expected,
        }, "--worker")
    tracked = (
        "re/tooling/sw2026/SdkPlanarGroupProcess.py",
        "re/tooling/sw2026/para/concentric/AssemblyModelExchange.py",
        "re/tooling/sw2026/para/concentric/ExchangeMateEndpoints.py",
        "re/solidworks/WriterResearch/ExchangePack.py",
        "re/solidworks/v2026/corpus/assemblies/Manifest.json",
        "re/solidworks/v2026/corpus/assembly-synchronized/Manifest.json",
        "re/solidworks/measurements/2026/D01ModelExchange01.json",
        "re/solidworks/measurements/2026/ExchangeMateEndpoints01.json",
        *(str(HERE.with_name(name).relative_to(ROOT)) for name in ("NativePlanarExchange.py", "PlanarExchange.py", HERE.name)),
    )
    result = {
        "schema": "kit.sw2026.ordinary-planar-mate-exchange.v1", "base": BASE,
        "native_export_static": native, "disclosed_native": sources, "neutral_generated": generated,
        "file_sha256": {name: digest((ROOT / name).read_bytes()) for name in tracked},
        "guarded_host_processes": {"native_observation": 3, "neutral_archive_construction": 4, "neutral_exchange_construction": 4},
        "saved_source_used_for_generation": False, "heldout_inputs_read": 0,
        "native_processes_started": 0, "native_acceptance": False, "public_writer_qualified": False,
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
