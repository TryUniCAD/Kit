import argparse
import hashlib
import json
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[4]
sys.path.insert(0, str(SCRIPT.parents[1]))
sys.path.insert(0, str(ROOT / "src"))

from Classes import registry
from CmgrBridge import load_cmgr
from Core import Obj
from NestedAssemblySourcePlan import CONTROL_SHA, ORACLE, checked, valid_sha
from ReferencePlaneReadRules import MODEL_SHA256, NEW_CLASSES, SERIALIZERS, VERSION, define_offset, project_offset, require
from ReferencePlaneSourcePlan import SCHEMA as CASE_SCHEMA, disclosed_cases, geometry
from RoundTrip import PLANS, stream_roundtrip, usage_summary
from Streams import load_rooted
from defs.ConfigPart import load_config, store_config_state
from defs.ResolvedCore import load_resolved, store_resolved
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


SCHEMA = "kit.sw2026.disclosed-offset-plane-audit.v1"
SOURCE_SCHEMA = "kit.sw2026.offset-plane-source-phases.v1"
DISCLOSED = ("D01", "D02", "D03", "D04")
CONFIG = "Contents/Config-0"
RESOLVED = CONFIG + "-ResolvedFeatures"
STREAMS = (CONFIG, RESOLVED, CONFIG + "-ModelHeader", "Header2", "Contents/CMgr", "Contents/CMgrHdr2")


class DisclosedReads:
    def __init__(self, source, selected):
        require(source.is_absolute(), "source-read custody requires an absolute packet")
        self.root = source.parent.resolve(strict=True)
        self.allowed = {self.root / "Source.json", self.root / "Disclosed.json"}
        self.native = set()
        self.observed_native = []
        self.denied = 0
        for case in disclosed_cases():
            if case["id"] not in selected:
                continue
            directory = self.root / "Disclosed" / case["id"]
            self.allowed.add(directory / "SavedAuthor.json")
            for suffix in ("", "Edited"):
                self.native.add(directory / "Native" / (case["name"] + suffix + ".SLDPRT"))
            for phase in ("author", "reopen"):
                self.allowed.add(self.root / "Progress" / case["id"] / phase / "Record.json")
        self.allowed.update(self.native)
        for phase in ("before", "after"):
            self.allowed.add(self.root / "Progress" / "D00" / phase / "Record.json")

    def observe(self, event, arguments):
        if event != "open" or not isinstance(arguments[0], (str, bytes)):
            return
        path = Path(arguments[0].decode() if isinstance(arguments[0], bytes) else arguments[0]).resolve()
        mode, flags = arguments[1:3]
        native = path.suffix.casefold() in (".sldprt", ".sldasm", ".slddrw", ".fcstd")
        protected = path.is_relative_to(self.root)
        allowed_tool = protected and path.parent == self.root / "Tools" and path.suffix == ".py"
        writing = isinstance(mode, str) and any(letter in mode for letter in "wax+") or bool(flags & 0x3)
        if native and path not in self.native or protected and path not in self.allowed and not allowed_tool or protected and writing:
            self.denied += 1
            raise PermissionError("source audit blocked a read outside its exact disclosed custody or a source write")
        if native:
            self.observed_native.append(path.relative_to(self.root).as_posix())

    def report(self):
        return {"allowed_disclosed_native_files": len(self.native), "native_open_events": len(self.observed_native),
                "distinct_native_files_opened": sorted(set(self.observed_native)), "denied_events": self.denied,
                "heldout_inputs_read": 0, "source_write_events": 0}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def value_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def read_json(path, root, expected=None):
    require(path.is_absolute() and path.resolve(strict=True).is_relative_to(root) and not path.is_symlink(),
            "disclosed source custody path escaped its declared packet")
    if expected is not None:
        checked(path, expected, root)
    return json.loads(path.read_bytes())


def source_packet(path, sha):
    require(path.is_absolute() and path.name == "Source.json" and valid_sha(sha),
            "an absolute frozen Source.json and exact digest are required")
    root = path.parent.resolve(strict=True)
    require(path.parent == root and not any(part in ("Holdouts", "PrivateInspection.json") for part in path.parts),
            "source audit requires a canonical disclosed packet path")
    packet = read_json(path, root, sha)
    require(packet["schema"] == SOURCE_SCHEMA and packet["oracle_sha256"] == ORACLE and packet["control_sha256"] == CONTROL_SHA and
            packet["writer_output_count"] == 0 and packet["native_acceptance"] is False and packet["heldout_designs_guest_private"] is True,
            "unexpected native reference-plane source packet")
    declared = read_json(root / "Disclosed.json", root, packet["disclosed_sha256"])
    require(declared == {"schema": CASE_SCHEMA, "cases": disclosed_cases()}, "declared disclosed source cases differ")
    require(packet["tools_sha256"], "native source tools are not hash locked")
    for name, sha256 in packet["tools_sha256"].items():
        require(Path(name).name == name and name.endswith(".py"), "invalid frozen source tool name")
        checked(root / "Tools" / name, sha256, root / "Tools")
    return root, packet


def phase_record(root, packet_sha, case_id, phase):
    require(case_id in (*DISCLOSED, "D00"), "sealed source phases are outside this audit")
    path = root / "Progress" / case_id / phase / "Record.json"
    record = read_json(path, root)
    require(record["schema"] == SOURCE_SCHEMA and record["packet_sha256"] == packet_sha and record["case_id"] == case_id and
            record["phase"] == phase and record["passed"] is True and record["stage"] == "passed",
            "native disclosed source phase did not qualify")
    return record, digest(path)


def qualified_case(root, packet_sha, case):
    records = [phase_record(root, packet_sha, case_id, phase) for case_id, phase in
               (("D00", "before"), (case["id"], "author"), (case["id"], "reopen"), ("D00", "after"))]
    rows = [row for row, sha in records]
    require(len({row["identity"]["process_creation_filetime"] for row in rows}) == 4 and
            all(first["finished_at"] <= second["started_at"] for first, second in zip(rows, rows[1:])),
            "native disclosed source lacks distinct ordered healthy brackets")
    before, author, reopen, after = rows
    require(author["native_artifact_manifest_sha256"] == reopen["native_artifact_manifest_sha256"],
            "disclosed author/reopen artifacts differ")
    case_root = root / "Disclosed" / case["id"]
    saved = read_json(case_root / "SavedAuthor.json", case_root, author["private_saved_snapshot_sha256"])
    require(saved["case"] == case and set(saved["result"]["saved_files"]) == {"source", "edited"} and
            value_hash(saved["artifact_manifest"]) == author["native_artifact_manifest_sha256"],
            "disclosed source snapshot differs from its immutable artifact manifest")
    paths = {"source": case_root / "Native" / (case["name"] + ".SLDPRT"),
             "edited": case_root / "Native" / (case["name"] + "Edited.SLDPRT")}
    for role, path in paths.items():
        identity = saved["result"]["saved_files"][role]
        require(identity["status"] == [True, 0, 0] and checked(path, identity["sha256"], case_root).stat().st_size == identity["bytes"],
                "disclosed native source sibling changed")
        require(saved["artifact_manifest"][role] == {key: identity[key] for key in ("bytes", "sha256")},
                "disclosed source artifact manifest does not identify the actual saved siblings")
    return saved, paths, {
        "phase_receipts_sha256": {key: sha for key, (row, sha) in zip(("before", "author", "reopen", "after"), records, strict=True)},
        "source_manifest_sha256": author["native_artifact_manifest_sha256"],
        "saved_snapshot_sha256": author["private_saved_snapshot_sha256"],
        "healthy_brackets": True, "distinct_native_processes": 4,
    }


def stream_reports(archive, rules):
    result = {}
    for name in STREAMS:
        row = stream_roundtrip(archive, name, rules, {**PLANS, **rules.plans}, linked=True)
        result[name] = {key: row.get(key) for key in ("passed", "bytes", "sha256", "map_base", "map_count", "tail", "error")}
        result[name]["schema_usage"] = usage_summary([row])
    return result


def read_root(archive, rules, name, class_name):
    if name == "Contents/CMgr":
        document, reader = load_cmgr(archive.require(name), rules, VERSION, archive=archive, name=name)
    else:
        document, reader = load_rooted(archive.require(name), rules, 1, VERSION)
    require(not document.tail and not reader.left() and len(document.roots) == 1,
            "source header or manager has an unread tail or a different root count")
    value, = document.roots
    require(isinstance(value, Obj) and value.cls == class_name, "source header or manager has a different root class")
    return value


def typed_projection(path, identity, case, edited, snapshot, rules):
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == identity["sha256"] and len(raw) == identity["bytes"], "native source changed before typed projection")
    archive = SldprtArchive.from_bytes(raw, path)
    require(archive.format_version == 4 and ContainerMo(archive.streams) == VERSION,
            "offset source audit supports only native container 4 / model 19000")
    reports = stream_reports(archive, rules)
    result = {"sha256": identity["sha256"], "bytes": identity["bytes"], "streams": reports, "typed_slots_passed": False}
    if not all(row["passed"] for row in reports.values()):
        result["error"] = "one or more linked source stream codecs did not consume and reproduce the exact streams"
        return result
    configuration, config_map = load_config(archive.require(CONFIG), rules, VERSION, archive=archive, name=CONFIG)
    resolved, resolved_map = load_resolved(archive.require(RESOLVED), rules, VERSION, archive=archive, name=RESOLVED, seed=config_map.map_state())
    require(not configuration.tail and not resolved.tail and resolved_map.base == config_map.count,
            "source archive has an unread tail or discontinuous Config/Resolved map")
    config_bytes, seed = store_config_state(configuration, rules, VERSION)
    require(config_bytes == archive.require(CONFIG) and store_resolved(resolved, rules, VERSION, seed=seed) == archive.require(RESOLVED),
            "source archive loses object identity through the re-emitted configuration seed")
    model, = configuration.roots
    require(isinstance(model, Obj) and model.cls == "moPart_c", "source configuration is not a typed part")
    expected = geometry(case, edited)
    result["projection"] = project_offset(model, resolved.roots, resolved_map, case, expected, snapshot)
    result["typed_slots_passed"] = result["projection"]["slot_correlations_passed"]
    manager = read_root(archive, rules, "Contents/CMgr", "moConfigurationMgr_c")
    top_header = read_root(archive, rules, "Header2", "moHeader_c")
    model_header = configuration.head["model_header"]
    result["map"] = {"config_base": config_map.base, "config_count": config_map.count,
                     "resolved_base": resolved_map.base, "resolved_count": resolved_map.count,
                     "context": resolved.head["context"], "re_emitted_seed_continuity": True}
    result["headers"] = {"model_update": model_header["f40"], "top_update": top_header["f40"],
                         "configuration_update": manager["f360"]["f860"]}
    require(path.read_bytes() == raw, "typed source audit changed an immutable native sibling")
    return result


def audit_case(root, packet_sha, case, rules):
    saved, paths, qualification = qualified_case(root, packet_sha, case)
    result = {"case_id": case["id"], "source_qualification": qualification, "siblings": {}, "passed": False}
    for role, edited in (("source", False), ("edited", True)):
        snapshot = saved["result"]["edited" if edited else "initial"]
        try:
            result["siblings"][role] = typed_projection(paths[role], saved["result"]["saved_files"][role], case, edited, snapshot, rules)
        except Exception as error:
            result["siblings"][role] = {"sha256": saved["result"]["saved_files"][role]["sha256"], "typed_slots_passed": False, "error": repr(error)}
    result["passed"] = all(row["typed_slots_passed"] for row in result["siblings"].values())
    if result["passed"]:
        original, edited = (result["siblings"][role]["projection"] for role in ("source", "edited"))
        result["edit_checks"] = {
            "plane_feature_identity_preserved": original["plane_feature_id"] == edited["plane_feature_id"],
            "selected_principal_preserved": original["support_feature_id"] == edited["support_feature_id"],
            "ordered_slot_classes_preserved": [None if row is None else row["class"] for row in original["ordered_geometry_slots"]] ==
                                             [None if row is None else row["class"] for row in edited["ordered_geometry_slots"]],
            "distance_changed_by_declared_edit": original["ordered_geometry_slots"][0]["distance_m"] != edited["ordered_geometry_slots"][0]["distance_m"],
            "stored_origin_changed": original["common_plane"]["root_m"] != edited["common_plane"]["root_m"],
            "boss_depth_unchanged": original["boss_depth_m"] == edited["boss_depth_m"],
        }
        result["passed"] = all(result["edit_checks"].values())
    for role, path in paths.items():
        checked(path, saved["result"]["saved_files"][role]["sha256"], path.parent)
    result["source_assets_unchanged"] = True
    return result


def source_fingerprints():
    result = {}
    for module in tuple(sys.modules.values()):
        file = getattr(module, "__file__", None)
        if file is None:
            continue
        path = Path(file).resolve()
        if path.suffix == ".py" and path.is_relative_to(ROOT) and path.is_file():
            result[path.relative_to(ROOT).as_posix()] = digest(path)
    return dict(sorted(result.items()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--case", choices=DISCLOSED, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(len(set(args.case)) == len(args.case), "a disclosed source case may be selected only once")
    custody = DisclosedReads(args.packet, args.case)
    sys.addaudithook(custody.observe)
    root, packet = source_packet(args.packet, args.packet_sha256)
    require(args.output.is_absolute() and args.output.parent.resolve(strict=True) == args.output.parent and
            not args.output.exists() and not args.output.is_relative_to(root), "choose an unused absolute audit receipt outside the source packet")
    rules = define_offset(registry())
    cases = {row["id"]: row for row in disclosed_cases()}
    result = {"schema": SCHEMA, "packet_sha256": args.packet_sha256, "selected_disclosed_cases": args.case,
              "native_model_module_sha256": MODEL_SHA256, "new_class_serializers": SERIALIZERS,
              "new_provisional_schemas": list(NEW_CLASSES), "cases": [], "passed": False,
              "heldout_inputs_read": 0, "native_processes_started": 0, "writer_output_count": 0,
              "generated_native_acceptance": False, "codec_roundtrip_is_not_generation": True}
    for case_id in args.case:
        result["cases"].append(audit_case(root, args.packet_sha256, cases[case_id], rules))
    result["passed"] = all(row["passed"] for row in result["cases"])
    result["source_read_custody"] = custody.report()
    result["code_fingerprints"] = source_fingerprints()
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"sha256": digest(args.output), "passed": result["passed"], "disclosed_cases": args.case,
                      "heldout_inputs_read": 0, "writer_output_count": 0}))
    raise SystemExit(0 if result["passed"] else 3)


if __name__ == "__main__":
    main()
