import json
from pathlib import Path, PureWindowsPath

from AuthorCurves import digest, require
from InspectSdkPlanarGroup import ORACLE, TOOLS as GROUP_TOOLS


SCHEMA = "kit.sw2026.original-planar-sdk-evaluation.v1"
SOURCE_LOCK = "8f79ed2aa8559b7186f414330b495ce50c4fa3612f69d421bbd7bc83037ca417"
SOURCE_SPECS = "642066a5493d58c09e68e5965b315c741c56be75541e53d17f66077a5d0909d8"
DISCLOSED_NATIVE = "333574efef8ac855ccb4b2a4a933b48e386ccbb03aa995d9c975e9a3c2c5198b"
PUBLIC_READ = "035c1c2d8b9ea86b624649ae54ce7230a41d500cfbd4807ebeb4b92f64ccc7c7"
SLOTS = {"Slot01": "A20HeldoutPlaneCoincidentDistance", "Slot02": "A21HeldoutPlaneParallelDistance"}
TOOLS = tuple(dict.fromkeys((*GROUP_TOOLS, "ReadSdkOrderedNative.py", "ReadSdkPlanarGroupNative.py", "OriginalPlanarNames.py", "OriginalPlanarRecipe.py", "OriginalPlanarProcess.py", "CheckOriginalPlanarMethod.py", "OriginalPlanarEvaluation.py", "FreezeOriginalPlanarEvaluation.py", "RunOriginalPlanarEvaluation.py", "InspectOriginalPlanarSlot.py")))


def checked(path, wanted):
    require(path.is_file() and not path.is_symlink() and digest(path) == wanted, "a frozen original-planar custody identity differs: " + path.name)
    return path


def guest_path(value, name=None, local=False):
    require(type(value) is str, "guest locators must contain strings only")
    path = PureWindowsPath(value)
    require(path.is_absolute() and ".." not in path.parts and (name is None or path.name == name), "the original evaluation has an invalid guest locator")
    if local:
        require(path.drive.upper() == "C:" and not path.root.startswith("\\\\"), "private original-evaluation output must be on the guest-local C drive")
    return str(path)


def verify_locators(locators):
    require(set(locators) == {"schema", "specs_guest_path", "private_guest_root", "control", "slots"} and locators["schema"] == "kit.sw2026.original-planar-guest-locators.v1", "the original-evaluation locators have unsupported state")
    guest_path(locators["specs_guest_path"], "AssemblyMateSourceSpecs01.json")
    guest_path(locators["private_guest_root"], local=True)
    require(set(locators["slots"]) == set(SLOTS) and set(locators["control"]) == {"parent_guest_path", "child_guest_path"}, "the original evaluation requires exactly two opaque source slots and disclosed controls")
    guest_path(locators["control"]["parent_guest_path"], "A22CombinedRotated.SLDASM")
    guest_path(locators["control"]["child_guest_path"], "CohortChild.SLDPRT")
    for slot, name in SLOTS.items():
        row = locators["slots"][slot]
        require(set(row) == {"public_name", "parent_guest_path", "child_guest_path"} and row["public_name"] == name, "the opaque slot differs from its public source lock identity")
        guest_path(row["parent_guest_path"], name + ".SLDASM")
        guest_path(row["child_guest_path"], "CohortChild.SLDPRT")
        require(PureWindowsPath(row["parent_guest_path"]).parent == PureWindowsPath(row["child_guest_path"]).parent, "the source lock requires its actual immutable owned sibling")


def verify(packet, wanted):
    job = json.loads(checked(packet, wanted).read_bytes())
    root = packet.parent
    require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE and job["source_lock_sha256"] == SOURCE_LOCK and job["specs_sha256"] == SOURCE_SPECS and job["heldout_inputs_read"] == 0 and job["native_acceptance"] is False and job["source_access_requires_explicit_release"] is True, "expected the frozen source-unexposed original evaluation method")
    require(Path(__file__).resolve().parent == (root / "Tools").resolve(strict=True) and set(job["tools_sha256"]) == set(TOOLS), "run only the complete frozen original-evaluation tool closure")
    for name, value in job["tools_sha256"].items():
        checked(root / "Tools" / name, value)
    dependencies = json.loads(checked(root / "DependencyLock.json", job["dependency_lock_sha256"]).read_bytes())
    require(set(dependencies["files_sha256"]) == {"pyproject.toml", "uv.lock"}, "the evaluation must retain its exact declared dependency lock")
    for name, value in dependencies["files_sha256"].items():
        checked(root / "Dependencies" / name, value)
    manifest = json.loads(checked(root / "CodeManifest.json", job["code_manifest_sha256"]).read_bytes())
    source_root = root / "CodeRoot"
    for name, value in manifest["files"].items():
        relative = Path(name)
        require(not relative.is_absolute() and ".." not in relative.parts and relative.suffix == ".py", "the frozen writer closure contains an invalid source path")
        checked(source_root / relative, value["sha256"])
    require(digest(root / "CodeManifest.json") == job["method_source_manifest_sha256"], "the constructor must use the exact disclosed method source closure")
    method = json.loads(checked(root / "MethodResult.json", job["method_result_sha256"]).read_bytes())
    require(method["passed"] and method["source_manifest_sha256"] == job["method_source_manifest_sha256"] and method["source_frozen_before_semantic_projection"] and method["source_unchanged"] and method["heldout_inputs_read"] == method["native_processes_started"] == 0 and method["distinct_successful_workers"] == 12 and method["rejecting_worker_invocations"] == 7 and all(row["passed"] for row in method["cases"] + method["negative_cases"]), "the disclosed names/recipe process rehearsal is not qualified")
    native = json.loads(checked(root / "DisclosedNative.json", DISCLOSED_NATIVE).read_bytes())
    public = json.loads(checked(root / "DisclosedPublicRead.json", PUBLIC_READ).read_bytes())
    require(native["passed"] and native["controls_healthy"] and native["distinct_processes"] == 4 and native["heldout_inputs_read"] == 0 and public["passed"] and public["typed_stream_round_trips"] == 26 and public["heldout_inputs_read"] == public["native_processes_started"] == 0, "the disclosed native lifecycle or exact public saved readback is not qualified")
    source = json.loads(checked(root / "SourceLock.json", SOURCE_LOCK).read_bytes())
    require(source["passed"] and source["controls_healthy"] and source["heldout_results_sealed"] and source["specs_sha256"] == SOURCE_SPECS and source["writer_output_count"] == 0, "the pre-writer native source lock is not qualified")
    rows = {row["name"]: row for row in source["cases"] if row["split"] == "heldout"}
    require(set(rows) == set(SLOTS.values()) and all(row["passed"] for row in rows.values()), "both original source identities must already be locked")
    locators = json.loads(checked(root / "Locators.json", job["locators_sha256"]).read_bytes())
    verify_locators(locators)
    control = json.loads(checked(root / "ControlCase.json", job["control_case_sha256"]).read_bytes())
    require(control["case"]["name"] == "A22CombinedRotated" and control["child_size_m"] == [.04, .02, .01], "the exact disclosed A22 control recipe differs")
    return job, locators, rows, source_root, control
