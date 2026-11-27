from argparse import ArgumentParser
from functools import partial
import json
import math
from pathlib import Path, PureWindowsPath
import subprocess
import sys

from ObserveVendorBossCorpus import (
    demand, digest, inspect_saved, observe_part, phase, read_json, save_current, verify_part, write_json,
)
from ObserveVendorBossPresentation import (
    OPEN_READ_ONLY_SILENT, observe_annotations, observe_display, observe_lights, observe_material,
)


DISPLAY_PLANES = 5
NO_DOCUMENT_OPTION = 0
ROLES = ("ControlBefore", "Author", "NoOp", "Toggled", "ControlAfter")
GEOMETRY_MEASUREMENTS = ("volume_m3", "area_m2", "centre_of_mass_m", "mass_kg", "bounds_m")


def observe(base, document):
    member = base.member
    extension = document.Extension
    configuration = document.ConfigurationManager.ActiveConfiguration
    return {
        **observe_part(base, document),
        "read_only": bool(member(document, "IsOpenedReadOnly")),
        "annotation_views": observe_annotations(extension, member),
        "lights": observe_lights(document, member),
        "display": observe_display(document, extension, configuration, member),
        "document_display_planes_preference": bool(extension.GetUserPreferenceToggle(DISPLAY_PLANES, NO_DOCUMENT_OPTION)),
        "material": observe_material(document, extension, configuration, member),
    }


def check_plane_flag(state, expected):
    native = state["display"]["construct_planes_visible"]
    preference = state["document_display_planes_preference"]
    demand(native == preference == expected, f"plane document getters differ: {native!r}, {preference!r}, expected {expected!r}")


def other_state(state):
    view = {key: value for key, value in state["display"].items() if key != "construct_planes_visible"}
    result = {
        key: value for key, value in state.items()
        if key not in ("display", "document_display_planes_preference", "read_only")
    }
    return {**result, "display": view}


def same_measurements(left, right, *, toggle=False, ignore_read_only=False):
    def semantic(state):
        value = other_state(state) if toggle else state
        fields = {key: item for key, item in value.items()
                  if key not in GEOMETRY_MEASUREMENTS and (not ignore_read_only or key != "read_only")}
        return json.dumps(fields, sort_keys=True, separators=(",", ":"), allow_nan=False)

    def numbers(value):
        return value if isinstance(value, (list, tuple)) else (value,)

    return semantic(left) == semantic(right) and all(
        math.isclose(a, b, rel_tol=1e-8, abs_tol=1e-12)
        for key in GEOMETRY_MEASUREMENTS
        for a, b in zip(numbers(left[key]), numbers(right[key]), strict=True)
    )


def capture(base, app, request, result):
    source = Path(request["path"]).resolve(strict=True)
    demand(digest(source) == request["sha256"], "retained authoring seed digest differs")
    folder = Path(request["work"]).resolve(strict=True)
    resumed = request.get("resumed_no_op")
    if resumed:
        working = Path(resumed["working"]).resolve(strict=True)
        demand(digest(working) == resumed["sha256"], "warmed working copy digest differs")
    else:
        working = folder / "Working" / "PlaneVisibilityProbe.SLDPRT"
        working.parent.mkdir()
        with working.open("xb") as stream:
            stream.write(source.read_bytes())
        demand(digest(working) == request["sha256"], "writable copy digest differs")
    errors, warnings = base.statuses()
    document = app.OpenDoc6(str(working), 1, 1, "", errors, warnings)
    result.update(open_errors=errors.value, open_warnings=warnings.value)
    demand(document is not None, f"SOLIDWORKS could not open the task copy: {errors.value}")
    points = tuple(map(tuple, request["profile_m"]))
    captures = result["snapshots"] = {}
    title = str(base.member(document, "GetTitle"))

    def snapshot(role):
        status = save_current(base, document)
        state = observe(base, document)
        verify_part(base, state, points, request["depth_m"], None)
        demand(str(base.member(document, "GetTitle")) == title, "owned document title changed")
        out = folder / role / working.name
        out.parent.mkdir()
        with out.open("xb") as stream:
            stream.write(working.read_bytes())
        captures[role] = {
            "archive": f"{role}/{working.name}", "sha256": digest(out), "bytes": out.stat().st_size,
            "saved": status, "observation": state,
        }
        return state

    try:
        demand(errors.value == warnings.value == 0, "SOLIDWORKS reported load errors or warnings")
        demand(PureWindowsPath(str(base.member(document, "GetPathName"))) == PureWindowsPath(str(working)),
               "SOLIDWORKS opened a path other than the task copy")
        initial = result["initial"] = observe(base, document)
        demand(not initial["read_only"], "owned authoring copy opened read-only")
        check_plane_flag(initial, request["initial_visibility"])
        verify_part(base, initial, points, request["depth_m"], None)
        if resumed:
            noop = resumed["observation"]
            demand(same_measurements(initial, noop), "reopened warm copy differs from the original no-op reading")
        else:
            result["warm_rebuild_succeeded"] = bool(document.ForceRebuild3(False))
            demand(result["warm_rebuild_succeeded"], "unchanged source did not rebuild")
            result["warm_save"] = save_current(base, document)
            before, noop = snapshot("Before"), snapshot("NoOp")
            demand(same_measurements(initial, before) and same_measurements(before, noop),
                   "presentation or geometry changed during warm no-op saves")
        target = not request["initial_visibility"]
        result["mutation"] = {
            "method": "IModelDocExtension.SetUserPreferenceToggle", "preference": DISPLAY_PLANES,
            "option": NO_DOCUMENT_OPTION, "requested_value": target,
        }
        reported = document.Extension.SetUserPreferenceToggle(DISPLAY_PLANES, NO_DOCUMENT_OPTION, target)
        result["mutation"]["return_value"] = bool(reported)
        result["after_set"] = changed = observe(base, document)
        check_plane_flag(changed, target)
        demand(same_measurements(changed, noop, toggle=True), "another semantic field changed during the setter")
        result["toggle_rebuild_succeeded"] = bool(document.ForceRebuild3(False))
        demand(result["toggle_rebuild_succeeded"], "toggled source did not rebuild")
        result["after_toggle_rebuild"] = rebuilt = observe(base, document)
        demand(same_measurements(rebuilt, changed), "toggled state changed during rebuild")
        demand(same_measurements(snapshot("Toggled"), changed), "toggled state changed during save")
    finally:
        app.QuitDoc(str(base.member(document, "GetTitle")))
    demand(digest(source) == request["sha256"], "retained authoring seed changed")
    result["working_title"] = title
    result["final_working_sha256"] = digest(working)
    demand(result["final_working_sha256"] == captures["Toggled"]["sha256"], "closed working copy differs from saved snapshot")


def read_only_observation(base, document, *, path):
    state = observe(base, document)
    demand(state["read_only"], "native document did not open read-only")
    demand(PureWindowsPath(str(base.member(document, "GetPathName"))) == path,
           "SOLIDWORKS opened a path other than the requested snapshot")
    return state


def inspect(base, app, request, result):
    if request.get("capture"):
        capture(base, app, request, result)
        return
    path = PureWindowsPath(str(Path(request["path"]).resolve(strict=True)))
    probe = partial(read_only_observation, path=path)
    inspect_saved(base, app, request, result, observe=probe, open_options=OPEN_READ_ONLY_SILENT)
    for state_name in ("initial", "rebuilt"):
        check_plane_flag(result[state_name], request["initial_visibility"])
    demand(same_measurements(result["initial"], result["rebuilt"]), "observed native state changed during read-only rebuild")


def stream_contrast(root, working, snapshots):
    sys.path.insert(0, str(root / "src"))
    from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Container.Archive import ContainerMo
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    clear, locators = {}, {}
    for role, (folder, snapshot) in snapshots.items():
        path = folder / snapshot["archive"]
        demand(digest(path) == snapshot["sha256"], f"{role} saved snapshot differs")
        parsed = SldprtArchive.OpenAction(path)
        clear[role] = parsed.Streams
        version = ContainerMo(parsed.Streams)
        demand(version == 19000, "snapshot archive generation differs")
        fields = ReadHeaderGraph(parsed.Require("Header2"), version).FieldsValue
        locators[role] = PureWindowsPath(GetFileRef(fields["f38"]).PathValue)
    demand(all(locator == PureWindowsPath(str(working)) for locator in locators.values()),
           "stored snapshot locators differ from the single warmed working path")

    def diff(left, right):
        first, second = clear[left], clear[right]
        return sorted(name for name in set(first) | set(second) if first.get(name) != second.get(name))

    noise = diff("Before", "NoOp")
    changed = diff("NoOp", "Toggled")
    return {
        "same_encoded_locator": True, "clear_stream_counts": {role: len(streams) for role, streams in clear.items()},
        "no_op_changed_streams": noise, "toggle_changed_streams": changed,
        "changed_streams_outside_no_op_set": sorted(set(changed) - set(noise)),
    }


def reuse_preflight(report, expected_sha, plan, plan_sha, executable_sha):
    demand(digest(report) == expected_sha, "original preflight digest differs")
    prior = read_json(report)
    demand(prior["plan_sha256"] == plan_sha and prior["executable_sha256"] == executable_sha
           and not prior["passed"] and prior["controls_healthy"] and prior["distinct_owned_lifetimes"] == 3,
           "original preflight scope differs")
    rows = prior["phases"]
    demand(tuple(rows) == ("ControlBefore", "Author", "ControlAfter"), "original preflight roles differ")
    for role, row in rows.items():
        folder = report.parent / role
        request = read_json(folder / "Request.json")
        record = read_json(folder / "Record.json")
        source = plan["AuthorSeed" if role == "Author" else "Control"]
        demand(digest(folder / "Record.json") == row["record_sha256"]
               and digest(folder / "Request.json") == row["request_sha256"]
               and all(row[key] == value for key, value in record.items())
               and digest(Path(request["path"])) == row["source_sha256"] == source["sha256"],
               f"{role} preflight custody differs")
        demand(row["open_errors"] == row["open_warnings"] == row["exit"]["exit_code"] == 0
               and row["oracle_identity"]["build"] == plan["oracle_build"]
               and row["oracle_identity"]["sha256"] == executable_sha,
               f"{role} preflight native lifetime differs")
    author = rows["Author"]
    demand(not author["passed"] and author["error"] == "ValueError: presentation or geometry changed during warm no-op saves"
           and "mutation" not in author and author["warm_rebuild_succeeded"], "unexpected original preflight stop")
    folder = report.parent / "Author"
    retained = {role: (folder, sample) for role, sample in author["snapshots"].items()}
    before, noop = (retained[role][1] for role in ("Before", "NoOp"))
    for _, sample in retained.values():
        demand(digest(folder / sample["archive"]) == sample["sha256"] and sample["saved"]["saved"], "preflight snapshot differs")
        check_plane_flag(sample["observation"], plan["AuthorSeed"]["initial_visibility"])
    demand(same_measurements(before["observation"], noop["observation"]), "native preflight no-op states differ")
    demand(rows["ControlBefore"]["rebuilt"] == rows["ControlAfter"]["rebuilt"], "original stock controls disagree")
    working = folder / "Working" / "PlaneVisibilityProbe.SLDPRT"
    demand(digest(working) == noop["sha256"], "preflight working path no longer has the exact no-op bytes")
    return rows["ControlAfter"], working, retained


def measure(args):
    plan = read_json(args.plan)
    plan_sha = digest(args.plan)
    inputs = (plan["Control"], plan["AuthorSeed"])
    for source in inputs:
        demand(digest(Path(source["path"]).resolve(strict=True)) == source["sha256"], "frozen source digest differs")
    demand(inputs[0]["sha256"] != inputs[1]["sha256"], "control and author seed must be independent")
    root = args.root.resolve(strict=True)
    exe = args.executable.resolve(strict=True)
    demand(digest(exe) == args.executable_sha256, "licensed oracle executable differs")
    output = args.output.resolve()
    results = {}
    demand(bool(args.preflight) == bool(args.preflight_sha256), "preflight continuation requires a report and digest")
    author_options = {"capture": True}
    working = output / "Author" / "Working" / "PlaneVisibilityProbe.SLDPRT"
    snapshots = {}
    if args.preflight:
        leading, working, snapshots = reuse_preflight(args.preflight.resolve(strict=True), args.preflight_sha256,
                                                      plan, plan_sha, args.executable_sha256)
        results["ControlBefore"] = {**leading, "reused_preflight_role": "ControlAfter"}
        author_options["resumed_no_op"] = {"working": str(working), **snapshots["NoOp"][1]}
    output.mkdir()

    def run(role, source, **options):
        folder = output / role
        folder.mkdir()
        request, response = folder / "Request.json", folder / "Record.json"
        demand(digest(Path(source["path"])) == source["sha256"], f"{role} input digest differs")
        write_json(request, {
            **source, "role": role, "operation": "measure", "property": None, "executable": str(exe),
            "executable_sha256": args.executable_sha256, "work": str(folder), **options,
        })
        command = (sys.executable, "-B", str(Path(__file__)), "--root", str(root), "phase", str(request), str(response))
        with (folder / "Worker.log").open("xb") as log:
            try:
                worker = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=180, check=False)
            except subprocess.TimeoutExpired:
                results[role] = {"passed": False, "error": "owned worker exceeded 180 seconds"}
                return False
        if not response.is_file():
            results[role] = {"passed": False, "error": "owned worker produced no record", "worker_exit_code": worker.returncode}
            return False
        row = read_json(response)
        results[role] = row | {
            "request_sha256": digest(request), "record_sha256": digest(response), "worker_exit_code": worker.returncode,
            "source_sha256": source["sha256"], "source_unchanged": digest(Path(source["path"])) == source["sha256"],
        }
        return row["passed"] and worker.returncode == 0 and results[role]["source_unchanged"]

    before = bool(results) or run("ControlBefore", inputs[0])
    authored = before and run("Author", inputs[1], **author_options)
    if authored:
        author_folder = output / "Author"
        snapshots.update({role: (author_folder, sample) for role, sample in results["Author"]["snapshots"].items()})
        for role in ("NoOp", "Toggled"):
            folder, sample = snapshots[role]
            run(role, inputs[1] | {
                "path": str(folder / sample["archive"]), "sha256": sample["sha256"],
                "initial_visibility": inputs[1]["initial_visibility"] if role == "NoOp" else not inputs[1]["initial_visibility"],
            })
    after = run("ControlAfter", inputs[0])
    checks = {}
    if before and after:
        checks["controls_agree"] = same_measurements(results["ControlBefore"]["rebuilt"], results["ControlAfter"]["rebuilt"])
    if authored and all(results[role]["passed"] for role in ("NoOp", "Toggled")):
        reopened = [results[role]["rebuilt"] for role in ("NoOp", "Toggled")]
        captured = [snapshots[role][1]["observation"] for role in ("NoOp", "Toggled")]
        checks["non_target_semantics_unchanged"] = same_measurements(*reopened, toggle=True) and all(
            same_measurements(fresh, prior, ignore_read_only=True)
            for fresh, prior in zip(reopened, captured, strict=True)
        )
    fault = None
    if authored:
        try:
            checks["clear_stream_contrast"] = stream_contrast(root, working, snapshots)
        except (ValueError, KeyError) as error:
            fault = f"{type(error).__name__}: {error}"
    identities = [row["oracle_identity"] for row in results.values() if "oracle_identity" in row]
    births = {(row["pid"], row["started"]) for row in identities}
    passed = (
        len(births) == len(results) == len(ROLES) and all(row["build"] == plan["oracle_build"] for row in identities)
        and all(row["passed"] and row["worker_exit_code"] == 0 and row["source_unchanged"] for row in results.values())
        and checks.get("controls_agree") and checks.get("non_target_semantics_unchanged") and not fault
        and all(digest(Path(source["path"])) == source["sha256"] for source in inputs) and digest(args.plan) == plan_sha
    )
    report = output / "Result.json"
    write_json(report, {
        "schema": "kit.sw2026.vendor-boss-plane-visibility.v1", "passed": bool(passed),
        "controls_healthy": bool(before and after and checks.get("controls_agree")), "executable_sha256": args.executable_sha256,
        "distinct_owned_lifetimes": len(births), "plan_sha256": plan_sha, "original_preflight_sha256": args.preflight_sha256,
        "method_sha256": {name: digest(Path(__file__).with_name(name)) for name in (
            Path(__file__).name, "ObserveVendorBossCorpus.py", "ObserveVendorBossPresentation.py",
        )},
        "checks": checks, "archive_check_fault": fault, "phases": results,
    })
    print(json.dumps({"passed": bool(passed), "result_sha256": digest(report), "phases": len(results), "archive_fault": fault}))
    return 0 if passed else 1


if __name__ == "__main__":
    parser = ArgumentParser(description="Measure one document-wide SOLIDWORKS construct-plane visibility change")
    parser.add_argument("--root", type=Path, required=True)
    modes = parser.add_subparsers(dest="mode", required=True)
    batch = modes.add_parser("measure")
    for argument in ("plan", "output", "executable"):
        batch.add_argument(f"--{argument}", type=Path, required=True)
    batch.add_argument("--executable-sha256", required=True)
    batch.add_argument("--preflight", type=Path)
    batch.add_argument("--preflight-sha256")
    worker = modes.add_parser("phase")
    worker.add_argument("request", type=Path)
    worker.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.mode == "phase":
        raise SystemExit(phase(args.root, read_json(args.request), args.output, inspect=inspect))
    raise SystemExit(measure(args))
