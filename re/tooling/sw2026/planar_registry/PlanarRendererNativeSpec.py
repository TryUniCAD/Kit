from copy import deepcopy
import json
import os
from pathlib import Path, PureWindowsPath

from PlanarRegistryBuild import file_sha, load, require


WRITER = "6c48ec66ba5b8a2ff75a4920bf414d988399a267"
SOURCE_TREE = "13d50879fea6470271c7a9b79e5a48a1168d8d35"
HOST_PROOF = "b86210a7e84994637e0a32fdb32e6b33b8f38c3e08a1c10eeed97e285ca0b754"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
SCHEMA = "kit.sw2026.planar-named-renderer-lifecycle.v1"
ENTRY = "re/tooling/sw2026/planar_registry/ObservePlanarRendererNative.py"
SHARE = PureWindowsPath(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover")
CHILD = "CohortChild.SLDPRT"
DRIVE = "D1@Boss-Extrude1"
CONTROL = "A22"
TRIALS = ("A20", "A21")
PHASES = ("ControlBefore", "A20Original", "A20Generated", "A20FreshReopen",
          "A21Original", "A21Generated", "A21FreshReopen", "ControlAfter")
SOURCES = {
    "A20": ("AssemblyMateSource02/A20HeldoutPlaneCoincidentDistance/author",
            "cc3b4267b0353b4f8b7a855d456dfe04aaa725b9f59873462aa1399843cb75bd",
            "31121fe7780b2e60840a68bf6c4eb01362b275533879dae44333a1c5d36ab115",
            "46d29bdc6b1478935d7c53f74cab10f2d95e6483f0db81545ef0aa318b9b4db8", .016375),
    "A21": ("AssemblyMateSource02/A21HeldoutPlaneParallelDistance/author",
            "476e37c3de6358bd687120a485b036f04cd4d488300f1287b794f2151803dff0",
            "e4bb77277f3ce27cde3892311724d1faac71ceb998fc74f765a084f8b16a51ff",
            "e8fae71fbd9403e2d4fcd9952606fda9876cdd551ce161f6afe029a104af643c", .023625),
    CONTROL: ("NativeMateComboSource04/Native/A22CombinedRotated/author",
              "fac5708432e569e787dfc00aa87fe08e5ef2d6830ec88f2d69525f8030d9fd1f",
              "b46e1e0f066db55730ce765cb2547b97ad1416e1ea0ceaa588bb8e819f727321",
              "b57b51e1a344da7fcbe7a06a756a65e674e356d480c78d4cf4b0a125970714a7", None),
}


def exact(path, value):
    require(path.is_file() and not path.is_symlink() and file_sha(path) == value,
            "the renderer packet lost its exact file: " + str(path))
    return path


def source(disclosed, slot):
    folder, parent_sha, child_sha, record_sha, depth = SOURCES[slot]
    directory = disclosed / folder
    name = directory.parent.name
    paths = {key: exact(directory / filename, expected) for key, filename, expected in (
        ("parent", name + ".SLDASM", parent_sha), ("child", CHILD, child_sha),
        ("record", "Record.json", record_sha))}
    record = json.loads(paths["record"].read_bytes())
    assembly = record["assembly_result"]
    actual = assembly["saved"]
    case = deepcopy(record["job"]["case"])
    require(case["name"] == name and record["passed"] and record["job"]["phase"] == "author"
            and assembly["native_sha256"] == parent_sha
            and assembly["synchronized_child"]["native_sha256"] == child_sha
            and assembly["oracle_identity"]["sha256"] == ORACLE,
            "the original exact-build parent and synchronized child differ")
    for authored, observed in zip(case["mates"], actual["mates"], strict=True):
        require(authored.get("name", observed["name"]) == observed["name"],
                "the author record has crossed ordered mate ownership")
        authored["name"] = observed["name"]
    initial = {"case": case, "child_size_m": [.04, .02, .01], "options": {
        "case": case, "assembly_configuration": "Default", "child_configuration": "Default",
        "child_parameters_m": {"D1@Sketch1": .04, "D2@Sketch1": .02, DRIVE: .01},
        "occurrence_names": [row["name"] for row in actual["occurrences"]]}}
    edited = deepcopy(initial)
    if depth is not None:
        edited["child_size_m"][2] = edited["options"]["child_parameters_m"][DRIVE] = depth
    evidence = {"case": slot, "parent": str(paths["parent"]), "child": str(paths["child"]),
                "parent_sha256": parent_sha, "child_sha256": child_sha,
                "native_record_sha256": record_sha}
    return paths, evidence, {"depth_edit_m": depth, "initial": initial, "edited": edited,
                            "source_parent_tree": actual["tree"], "source_mass": actual["mass"],
                            "child_update_stamp": assembly["synchronized_child"]["update_stamp"]}


def encoded(root_name, slot, basename):
    return str(SHARE / root_name / slot / "Working" / basename)


def verify(root, wanted):
    packet = load(root / "Packet.json", wanted)
    require(packet["schema"] == SCHEMA and packet["writer_revision"] == WRITER
            and packet["writer_src_tree"] == SOURCE_TREE and packet["host_renderer_proof_sha256"] == HOST_PROOF
            and packet["oracle_sha256"] == ORACLE and packet["native_acceptance"] is False
            and packet["new_heldout_credit"] == 0 and packet["writer_runtime_file_reads"] == 0,
            "use the exact disclosed frozen named-renderer packet")
    if os.name == "nt":
        require(root == Path(SHARE / root.name) and Path(__file__).resolve() == (
            root / "CodeRoot/re/tooling/sw2026/planar_registry/PlanarRendererNativeSpec.py").resolve(),
            "use the root-owned canonical Windows share and verified frozen entrypoint")
    code = root / "CodeRoot"
    manifest = load(root / "CodeManifest.json", packet["code_manifest_sha256"])
    require(manifest["writer_revision"] == WRITER and manifest["writer_src_tree"] == SOURCE_TREE
            and {path.relative_to(code).as_posix() for path in code.rglob("*") if path.is_file()}
            == set(manifest["files"]), "the staged runtime dependency set changed")
    for relative, digest in manifest["files"].items():
        exact(code / relative, digest)
    cases = {}
    require(set(packet["cases"]) == set(TRIALS) and packet["phases"] == list(PHASES),
            "the native trial requires both disclosed cases and both controls")
    for slot in (*TRIALS, CONTROL):
        original, sources, prediction = source(root.parent, slot)
        if slot == CONTROL:
            require(load(root / "Control.json", packet["control_sha256"]) == prediction,
                    "the disclosed A22 control prediction changed")
            cases[slot] = (original, prediction, {}, {}, {})
            continue
        row = packet["cases"][slot]
        target = root / slot
        require(load(target / "Prediction.json", row["prediction_sha256"]) == prediction,
                "native prediction no longer matches the authored source scope")
        request = load(target / "NeutralRequest.json", row["request_sha256"])
        require(request["native_parent"] == encoded(root.name, slot, original["parent"].name)
                and all(hex_value not in json.dumps(request) for hex_value in (
                    sources["parent_sha256"], sources["child_sha256"], sources["native_record_sha256"])),
                "the complete writer request did not preserve the destination and disclosed intent boundary")
        before = load(target / "RequestFreeze.json", row["request_freeze_sha256"])
        require(before == {"request_sha256": row["request_sha256"], "prediction_sha256": row["prediction_sha256"],
                          "writer_revision": WRITER, "constructor_invocations": 0},
                "the neutral request and separate prediction must predate construction")
        first, second = (load(target / name, digest) for name, digest in row["guarded_receipts"].items())
        require(first.pop("pid") != second.pop("pid") and first == second and first["runtime_input_reads"] == 0,
                "the same model must generate in two independently guarded processes")
        files = {key: exact(target / "FrozenGenerated" / original[key].name, artifact["sha256"])
                 for key, artifact in row["generated"].items()}
        require(set(files) == {"parent", "child"}
                and all(row["generated"][key] == first[key] for key in files)
                and all(files[key].stat().st_size == row["generated"][key]["bytes"] for key in files),
                "frozen generated archive bytes changed")
        preflight = load(target / "StrictHostRead.json", row["strict_host_read_sha256"])
        require(preflight["passed"] and all(preflight["stages"]["generated"]["sha256"][name]
                     == row["generated"][name]["sha256"] for name in files),
                "the exact guarded candidates lack their independent strict host readback")
        cases[slot] = (original, prediction, files, request, preflight)
    return packet, cases
