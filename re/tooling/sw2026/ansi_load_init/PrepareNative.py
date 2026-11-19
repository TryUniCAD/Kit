from argparse import ArgumentParser
from copy import deepcopy
from hashlib import sha256
from json import dumps, loads
from pathlib import Path, PureWindowsPath


def digest(raw):
    return sha256(raw).hexdigest()


def checked(path, sha):
    raw = path.read_bytes()
    if path.is_symlink() or digest(raw) != sha:
        raise ValueError(f"centreline input changed: {path}")
    return raw


def encode(value):
    return (dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()


def store(root, name, raw):
    path = root / name
    path.parent.mkdir(exist_ok=True, parents=True)
    with path.open("xb") as stream:
        stream.write(raw)
    return {"path": name, "bytes": len(raw), "sha256": digest(raw)}


def pick_prior_rows(join):
    rows = join["cases"]
    ownership = ("actual_child_file_alias", "actual_configuration_selection",
                 "actual_detail_selectors", "actual_display_folder_view_aliases",
                 "actual_matching_ui_owners",
                 "complete_child_byte_identity", "complete_definition_byte_identity",
                 "stored_normal_coordinate_preserved")
    if (len(rows) != 20 or join["complete_style_retention_passed"] is not False
            or join["native_geometry_lifecycle_passed"] is not True
            or any(any(row[k] is not True for k in ownership) for row in rows)):
        raise ValueError("prior drawing comparison did not retain its complete typed owners")
    value = {"left": 0x44000, "right": 0x144000, "path": "/drawing_details/f20"}
    origins = {}
    for row in rows:
        origin = row["actual_origin_profile_link"]
        if (not isinstance(origin, dict) or set(origin) != {"id", "creation_time"}
                or any(type(item) is not int or item < 0 for item in origin.values())
                or origin != origins.setdefault(row["case"], origin)):
            raise ValueError("the prior native states did not retain the same typed origin")
        expected = [value] if row["style_mode"] == "ansi" and row["phase"] != "constructed" else []
        if row["presentation_changes"] != expected or row["passed"] is not (not expected):
            raise ValueError("prior drawing comparison has a residual beyond the centreline mask")
    if sum(bool(row["presentation_changes"]) for row in rows) != 8:
        raise ValueError("prior drawing comparison did not measure both ANSI cases through each phase")
    return [{"case": row["case"], "phase": row["phase"], "changes": row["presentation_changes"]}
            for row in rows]


def prepare_case(root, old, prior_root, process, record, source_sha):
    name = old["name"].removesuffix("Initialized")
    case = deepcopy(old)
    case["name"] = name + "CenterlineInitialized"
    case["constructor_source"] = source_sha
    request = (process / f"{name}Load0.Request.json").read_bytes()
    first = loads((process / f"{name}Load0.stdout.json").read_bytes())
    repeated = loads((process / f"{name}Load1.stdout.json").read_bytes())
    if (first != repeated or first["passed"] is not True or first["mode"] != "ansi"
            or first["runtime_input_file_access_attempts"] != 0
            or first["sdk_research_imports"] != []):
        raise ValueError("frozen ANSI models did not repeat in the guarded writer process")
    prepared = loads((process / f"{name}LoadPrepare.stdout.json").read_bytes())
    if prepared["passed"] is not True or prepared["actual_origin_aliases"] is not True:
        raise ValueError("frozen ANSI models lack complete typed readback")
    prior_style = loads(checked(prior_root / old["expected_presentation"]["path"],
                                old["expected_presentation"]["sha256"]))
    expected = deepcopy(prior_style)
    expected["drawing_details"]["f20"] |= 0x100000
    if prepared["presentation"] != expected or first["presentation"] != expected:
        raise ValueError("generated ANSI style differs outside the centreline mask")
    case["expected_presentation"] = store(root, f"Expected/{name}.json", encode(expected))
    case["paths"] = {kind: first[f"native_{kind}_path"] for kind in ("child", "drawing")}
    normalized = PureWindowsPath(r"C:\KitAnsiLoadInit01") / name
    if any(PureWindowsPath(target).parent != normalized for target in case["paths"].values()):
        raise ValueError("generated files do not target the new task-owned native folder")
    case["files"] = {}
    for kind, extension in (("child", ".SLDPRT"), ("drawing", ".SLDDRW")):
        data = checked(process / f"{name}{extension}", record[f"{kind}_sha256"])
        if len(data) != record[f"{kind}_bytes"] or digest(data) != first[f"{kind}_sha256"]:
            raise ValueError("generated ANSI file changed after validation")
        case["files"][kind] = store(root, f"Generated/{name}/{kind}{extension}", data)
    intent = loads(request)["origin_request"]
    if (intent["part"]["settings"]["output"]["path_name"] != case["paths"]["child"]
            or intent["native"]["output"]["path_name"] != case["paths"]["drawing"]
            or intent["drawing_document"]["model_refs"]["$tuple"][0]["source_path"] != case["paths"]["child"]):
        raise ValueError("measured native path differs from neutral drawing intent")
    request_record = store(root, f"Provenance/{name}Request.json", request)
    return case, request_record


def main():
    parser = ArgumentParser(description="Freeze the centreline-specific ANSI native lifecycle packet")
    parser.add_argument("candidate", type=Path)
    parser.add_argument("process", type=Path)
    parser.add_argument("prior_packet", type=Path)
    parser.add_argument("prior_join", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--process-sha256", required=True)
    parser.add_argument("--prior-packet-sha256", required=True)
    parser.add_argument("--prior-join-sha256", required=True)
    args = parser.parse_args()
    code = Path(__file__).resolve().parents[1]
    root = args.output.resolve()
    if root.is_relative_to(code.parents[2]):
        raise ValueError("native packet must remain outside the checkout")
    manifest = checked(args.candidate / "SourceManifest.json", args.manifest_sha256)
    proof = checked(args.process / "Result.json", args.process_sha256)
    previous = checked(args.prior_packet, args.prior_packet_sha256)
    join = loads(checked(args.prior_join, args.prior_join_sha256))
    prior, report = loads(previous), loads(proof)
    if (join["packet_sha256"] != args.prior_packet_sha256
            or report["source_manifest_sha256"] != args.manifest_sha256
            or report["passed"] is not True or report["process_count"] != 34
            or report["heldout_acceptance"] is not False
            or report["source_original_admission"] is not False):
        raise ValueError("centreline packet lacks its bound source and two guarded comparisons")
    prior_rows = pick_prior_rows(join)
    prior_root = args.prior_packet.parent
    root.mkdir(exist_ok=False)
    custody = [
        store(root, "Provenance/SourceManifest.json", manifest),
        store(root, "Provenance/HostProcessResult.json", proof),
        store(root, "Provenance/PreviousObserverPacket.json", previous),
        store(root, "Provenance/PrepareNative.py", Path(__file__).read_bytes()),
        store(root, "Provenance/PriorComparisonSummary.json",
              encode({"raw_report_sha256": args.prior_join_sha256, "rows": prior_rows})),
    ]
    cases = []
    candidates = {row["name"]: row for row in report["cases"] if row["mode"] == "ansi"}
    for old in prior["cases"]:
        if old["style_mode"] == "ansi":
            case, request = prepare_case(root, old, prior_root, args.process,
                                         candidates[old["name"].removesuffix("Initialized")],
                                         args.manifest_sha256)
            cases.append(case)
            custody.append(request)
    if {(row["style_mode"], row["kind"]) for row in cases} != {("ansi", "corner"), ("ansi", "center")}:
        raise ValueError("both measured ANSI profiles are required")
    tools = {}
    for name, row in prior["tools"].items():
        data = (code / name).read_bytes() if name == "InspectAnsiDrawingLifecycle.py" else checked(prior_root / row["path"], row["sha256"])
        tools[name] = store(root, f"Tools/{name}", data)
    qualifier = "QualifyAnsiLifecycle.py"
    host = store(root, f"HostTools/{qualifier}", (code / "ansi_pair" / qualifier).read_bytes())
    control = prior["control"]
    packet = {
        **prior,
        "experiment": "drawing-centreline-initialization",
        "source_manifest_sha256": args.manifest_sha256,
        "base_commit": loads(manifest)["base_commit"],
        "process_result_sha256": args.process_sha256,
        "previous_observer_packet_sha256": args.prior_packet_sha256,
        "cases": cases,
        "expected_native_processes": 10,
        "custody": custody,
        "control": store(root, control["path"], checked(prior_root / control["path"], control["sha256"])),
        "tools": tools,
        "host_tools": {qualifier: host},
    }
    stored = store(root, "Packet.json", encode(packet))
    print(dumps({"passed": True, "cases": 2, "packet_sha256": stored["sha256"],
                 "qualifier_sha256": host["sha256"], "expected_native_processes": 10}))


if __name__ == "__main__":
    main()
