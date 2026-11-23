from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import subprocess
import sys


HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProveConfigHeaderExchange import (
    CASES, MODEL_EXCHANGE_STREAM, PRIOR, REPO, Image, checked, create, parent, preload, proof_guard,
    read_exchange_map, require, source_cases, windows_path, wire,
)
from ProveAssemblyMateDescriptor import MATES, contrast, require_refusal
from ProveD01PropertyTransport import disclosed_cases
from ExchangeMateEndpoints import project_exchange_mate_endpoints, project_exchange_target
from ExchangeMessagePack import ExchangeMap, encode_config_atom

from convert.adapters.solidworks.Archive.Exchange.ReadUnqlite import ReadUnqlite
from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.serialization.Deserialize import FromData


BASE = "eeef0365613f06dca3f755916c677c6a090d0bbb"
SOURCE_LOCK = "3c67d10789bbd681bfb99da712e1c6a035d78713b326c3048373ed4972198997"
RENAME_LOCK = "3639fb9d7fd6c40e10782b8b43ce000a63269adcdcd8230ef911d24c38fe8d39"
MODEL_SHA = "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"
KERNEL_SHA = "77b7376933f483eb5c1e3a93e22241f07a001a824023f5498d880d9b45fae594"


def digest(data):
    return sha256(data).hexdigest()


def native_windows(model_path, kernel_path):
    model, kernel = Image(model_path, MODEL_SHA), Image(kernel_path, KERNEL_SHA)
    literals = {0x4CE96470: b"target\0", 0x4CE96478: b"uda0\0", 0x4CDD9838: b" \0",
                0x4CDCB310: "@\0".encode("utf-16-le")}
    for address, expected in literals.items():
        require(model.read(address, address + len(expected)) == expected, "changed native field or separator")
    iat = model.imports()
    require(iat["0x4cd36d88"] == {
        "module": "sldgcu.dll", "name": "?getUDASingleFace@gcFace_w@@QEAA?AV?$vector@JV?$allocator@J@std@@@std@@XZ",
    } and iat["0x4cd316b0"]["name"].endswith("@J@Z"), "changed native signed-long face serializer")
    require(int.from_bytes(model.read(0x4CE9CA88, 0x4CE9CA90), "little") == 0x4B82EB60,
            "changed chain-component target virtual dispatch")
    ranges = (
        (model, "mate_order", 0x4BC80B00, 0x4BC80FF6),
        (model, "concentric_kind", 0x4BC80540, 0x4BC8064C),
        (model, "wrapper_dummy", 0x4B50E1D0, 0x4B50E821),
        (model, "target_base", 0x4B809E30, 0x4B80A359),
        (model, "chain_component_target", 0x4B82EB60, 0x4B82ECC6),
        (model, "reference_chain_string", 0x4C291460, 0x4C2919EE),
        (model, "face_uda_and_downstream_branch", 0x4B8096A0, 0x4B809C12),
        (kernel, "actual_face_integer_attributes", 0x439EDFA0, 0x439EE10E),
    )
    windows = {}
    for image, name, start, end in ranges:
        require(any((image.base + lo, image.base + hi) == (start, end) for lo, hi, _ in image.functions),
                "native unwind function boundary differs")
        windows[name] = {"start": hex(start), "end_exclusive": hex(end), "sha256": digest(image.read(start, end))}
    return {"sldmodu_sha256": MODEL_SHA, "sldgcu_sha256": KERNEL_SHA,
            "vocabulary_addresses": [hex(address) for address in literals], "selected_functions": windows}


def encode_map(value):
    require(type(value) is ExchangeMap and len(value.pairs) < 16, "endpoint map exceeds ordinary fixed-map profile")
    return bytes((0x80 + len(value.pairs),)) + b"".join(
        encode_config_atom(key) + (encode_map(item) if type(item) is ExchangeMap else encode_config_atom(item))
        for key, item in value.pairs
    )


def open_parent(parent_bytes):
    archive = SldprtArchive.from_bytes(parent_bytes)
    link = ReadNativeLink(archive, 0)
    mates = ()
    if MATES in archive.streams:
        mate_stream = archive.require(MATES)
        mates = ReadMatesMut(mate_stream, link.ResolvedValue).RootsValue
        require(WriteMatesMut(mates, link.ResolvedValue)[0] == mate_stream, "actual mate owners do not replay exactly")
    return archive, link.ConfigValue.RootValue, mates


def saved_mates(archive, expected_count):
    stream = archive.require(MODEL_EXCHANGE_STREAM)
    store = ReadUnqlite(stream)
    records = ((raw, read_exchange_map(raw)) for _, raw in store.Records)
    (raw, group), = (row for row in records if row[1].values("class") == ("moMateGroup_c", "moNodeList_c"))
    require(group.values("NumberMates") == ((expected_count,) if expected_count else ())
            and tuple(key for key, _ in group.pairs if key.startswith("Mate")) ==
            tuple(f"Mate{index}" for index in range(expected_count)), "exchange mate group differs from native linked count")
    maps = tuple(tuple(group.field(f"Mate{i}").field(f"Ref{j}") for j in range(2))
                 for i in range(expected_count))
    return raw, maps


def describe(ends):
    return tuple({"target": row.field("dummy").field("target"),
                  "uda0": next(iter(row.field("dummy").values("uda0")), None),
                  "map_bytes": len(encode_map(row)), "map_sha256": digest(encode_map(row))} for row in ends)


def compare_parent(parent_bytes, child, prior_path):
    archive, root, mates = open_parent(parent_bytes)
    raw, expected = saved_mates(archive, len(mates))
    notes = {}
    if child is not None:
        (mate,), (saved,) = mates, expected
        composed = project_exchange_mate_endpoints(root, mate, child, historical_keeper_locator=prior_path)
        require(composed == saved and all(raw.count(encode_map(row)) == 1 for row in composed),
                "computed target or UDA differs from its actual ordered native exchange map")
        notes["current_as_prior_refusal"] = require_refusal(
            lambda: project_exchange_mate_endpoints(root, mate, child), "different actual child keeper")
        notes["wrong_history_refusal"] = require_refusal(
            lambda: project_exchange_mate_endpoints(root, mate, child, historical_keeper_locator=str(
                PureWindowsPath(prior_path).parent / "Foreign" / PureWindowsPath(prior_path).name)),
            "different actual child keeper")
        notes["actual_concentric_ends"] = describe(composed)
    elif mates:
        for mate, endpoints in zip(mates, expected, strict=True):
            require_refusal(lambda: project_exchange_mate_endpoints(root, mate, b""), "expected concrete moMateConcentric")
            for wrapper, saved in zip(mate.FieldsValue["f410"], endpoints, strict=True):
                wrapper = wrapper["o"]
                component = wrapper.FieldsValue["f58"]
                require(wrapper.ClassValue.NameValue == "moPlaneRef_w"
                        and component.ClassValue.NameValue == "moCompRefPlane_c", "unqualified control reference")
                _, target = project_exchange_target(root, component)
                dummy = ExchangeMap((("class", "moCompRefPlane_c"),
                                     ("featureID", str(component.FieldsValue["ff0"]["f00"])), ("target", target)))
                require(saved == ExchangeMap((("class", "moPlaneRef_w"), ("dummy", dummy)))
                        and raw.count(encode_map(saved)) == 1, "disclosed planar target ownership differs")
        notes["plane_feature_ids"] = tuple(row[0].field("dummy").field("featureID") for row in expected)
        notes["face_uda_rows"] = 0
    else:
        notes["empty"] = not expected
    return {"parent_sha256": digest(parent_bytes), "child_sha256": digest(child) if child is not None else None,
            "mate_cell_size": len(raw), "mate_cell_sha256": digest(raw), "mate_count": len(mates), **notes}


def inspect_saved_sources(disclosures, prior, source_lock, rename_lock):
    paths = {case["id"]: case for case in disclosed_cases()}
    result = {}
    samples = {}
    for label, path, pin in source_cases(disclosures, prior):
        child = historical = None
        raw = checked(path, pin)
        if "/" in label:
            slot, phase = label.split("/")
            pins = source_lock["cases"][slot]["native_artifact_digests"][phase.lower()]
            require(pins["parent"]["sha256"] == pin, "crossed disclosed parent receipts")
            name = paths[slot]["child_name"] + ".SLDPRT"
            child = checked(path.with_name(name), pins["child"]["sha256"])
            historical = windows_path(path.parents[2] / "Working" / name)
            samples[label] = (raw, child, historical)
        elif label == "renamed_native":
            pins = rename_lock["native"]["synchronized_saved_pair"]
            require(pins["parent"]["sha256"] == pin, "crossed renamed control receipts")
            name = "IndependentNameCylinder.SLDPRT"
            child = checked(path.with_name(name), pins["child"]["sha256"])
            historical = windows_path(path.parents[2] / "Owned" / "Working" / name)
        result[label] = compare_parent(raw, child, historical)
    raw, _, historical = samples["D01/Source"]
    _, root, (mate,) = open_parent(raw)
    for label in ("D01/Edited", "D02/Source"):
        wrong_child = samples[label][1]
        result["D01/Source"][label + " crossed_child_refusal"] = require_refusal(
            lambda: project_exchange_mate_endpoints(root, mate, wrong_child, historical_keeper_locator=historical),
            "mate wrapper child update is stale" if label == "D01/Edited" else "same child filename")
    return result


def copied(node, **fields):
    return ArchiveNode(node.ClassValue, node.FieldsValue | fields)


def malformed(root, mate, child):
    first, second = (row["o"] for row in mate.FieldsValue["f410"])
    comp = first.FieldsValue["f58"]
    face = comp.FieldsValue["fe8"]
    wrong_face = copied(first, f58=copied(comp, fe8=copied(face, f70=face.FieldsValue["f70"] ^ 1)))
    live_rows = face.FieldsValue["f10"]
    side = live_rows[0]["f08"]
    side_ref = side.FieldsValue["f10"]
    keeper = side_ref["f10"]
    file = keeper.FieldsValue["f08"]
    foreign = copied(file, shared=dict(file.FieldsValue["shared"], f28=file.FieldsValue["shared"]["f28"] + 1))
    altered = copied(side, f10=dict(side_ref, f10=copied(keeper, f08=foreign)))
    wrong_keeper = copied(first, f58=copied(comp, fe8=copied(face, f10=[
        dict(live_rows[0], f08=altered), *live_rows[1:],
    ])))
    bounds = (
        ("wrong_order", copied(second, f7c=0), "actual ordered active wrapper"),
        ("foreign_mate_id", copied(second, f74=mate.FieldsValue["f08"] + 1), "actual ordered active wrapper"),
        ("stale_wrapper_epoch", copied(second, f08=second.FieldsValue["f08"] + 1), "child update is stale"),
        ("reused_occurrence", copied(second, f58=comp), "two distinct selected occurrence"),
    )
    reports = {}
    for name, wrapper, expected in bounds:
        bad = copied(mate, f410=[{"o": first}, {"o": wrapper}])
        reports[name] = require_refusal(lambda: project_exchange_mate_endpoints(root, bad, child), expected)
    bad = copied(mate, f410=[{"o": wrong_face}, {"o": second}])
    reports["crossed_face_tag"] = require_refusal(
        lambda: project_exchange_mate_endpoints(root, bad, child), "actual lateral kernel face identity")
    bad = copied(mate, f410=[{"o": wrong_keeper}, {"o": second}])
    reports["foreign_side_keeper"] = require_refusal(
        lambda: project_exchange_mate_endpoints(root, bad, child), "different actual child keeper")
    return reports


def worker(request):
    require(set(request) == {"document", "ambient", "destination", "epoch"},
            "exchange endpoint worker requires neutral geometry, mate, locator and authored epoch")
    original = FromData(request["document"])
    adjusted = contrast(original)
    for document in (original, adjusted):
        preload(document)
    attempts = proof_guard()
    reports = {}
    for label, document in (("persistence", original), ("renamed_reversed", adjusted)):
        args = document, None, request["ambient"], request["destination"], request["epoch"], None
        result = parent(create("persistence", args), None, None)
        child = result.ChildValue.BytesValue
        (mate,) = result.MateValues
        root = result.StateValue.RootValue
        ends = project_exchange_mate_endpoints(root, mate, child)
        _, decoded_root, (decoded_mate,) = open_parent(result.BytesValue)
        require(project_exchange_mate_endpoints(decoded_root, decoded_mate, child) == ends,
                "linked assembly readback changed actual endpoint maps")
        reports[label] = {"parent_sha256": digest(result.BytesValue), "child_sha256": digest(child), "ends": describe(ends)}
    one, two = reports["persistence"], reports["renamed_reversed"]
    require(one["child_sha256"] == two["child_sha256"] and one["parent_sha256"] != two["parent_sha256"]
            and tuple(row["uda0"] for row in one["ends"]) == tuple(row["uda0"] for row in two["ends"])
            and tuple(row["target"].split("@")[0] for row in two["ends"]) == ("Other-mount-3", "Motion-guide-17")
            and all(row["target"].endswith("@ConcentricNeutralAlphaDerived") for row in two["ends"]),
            "authored reversal and renaming changed child UDA or lost actual occurrence order")
    refusals = malformed(root, mate, child)
    require(not attempts, "exchange endpoint generation accessed external input")
    return {"models": reports, "refusals": refusals, "runtime_input_accesses": len(attempts)}


def main():
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--worker", action="store_true")
    group.add_argument("--disclosures", type=Path)
    parser.add_argument("--sldmodu", type=Path)
    parser.add_argument("--sldgcu", type=Path)
    options = parser.parse_args()
    if options.worker:
        sys.stdout.buffer.write(wire(worker(json.load(sys.stdin))))
        return
    require(options.sldmodu and options.sldgcu, "both exact build modules are required for static evidence")
    measurements = REPO / "re/solidworks/measurements/2026"
    saved = inspect_saved_sources(options.disclosures,
        json.loads(checked(measurements / "ConcentricD01PropertyTransport01.json", PRIOR)),
        json.loads(checked(measurements / "ConcentricMateSourceArchive01.json", SOURCE_LOCK)),
        json.loads(checked(measurements / "ComponentInstanceNameWire01.json", RENAME_LOCK)))
    packet, pin = CASES["persistence"]
    folder = options.disclosures / packet
    trial = json.loads(checked(folder / "Trial.json", pin))

    def intake(role):
        key = f"Evidence/{role}.json"
        return json.loads(checked(folder / key, trial["files_sha256"][key]))

    request = wire({"document": intake("Neutral"), "ambient": intake("Ambient"),
                    "destination": windows_path(folder / "Working" / trial["working_names"]["parent"]),
                    "epoch": intake("Build")["written_at"]})
    command = (sys.executable, "-I", "-B", str(HERE), "--worker")
    first, second = (subprocess.run(command, input=request, capture_output=True, timeout=90) for _ in range(2))
    require(first.returncode == second.returncode == 0 and first.stdout == second.stdout,
            (first.stderr + second.stderr).decode() or "guarded model workers differ")
    proof = json.loads(first.stdout)
    require(all(proof["models"]["persistence"][f"{role}_sha256"] == trial["generated_sha256"][role]
                for role in ("parent", "child")), "previous genuine persistence archive pair changed")
    receipt = {"schema": "kit.sw2026.exchange-mate-endpoints.v1", "base": BASE,
               "disclosed_source_sha256": SOURCE_LOCK, "renamed_source_sha256": RENAME_LOCK,
               "prior_parent_inventory_sha256": PRIOR, "prior_generated_pair_trial_sha256": pin,
               "exact_build": "34.5.2.0604", "native_static": native_windows(options.sldmodu, options.sldgcu),
               "saved_contrasts": saved, "generated": proof, "request_sha256": digest(request), "worker_processes": 2,
               "native_runs": 0, "heldout_accesses": 0,
               "proof_sha256": {path.name: digest(path.read_bytes()) for path in (
                   HERE, HERE.with_name("ExchangeMateEndpoints.py"))}}
    print(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
