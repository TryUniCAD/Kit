from argparse import ArgumentParser
from contextlib import redirect_stderr, redirect_stdout
import json
import os
from pathlib import Path, PureWindowsPath
import re
from shutil import copyfile

from AttachedTopBoxAuthor import BODY, PARAMETERS
from AuthorCurves import digest, require, write_json
from AuthorRectangleAnchors import CONTROL, ORACLE, control
from RunAttachedTopBoxSources import ORACLE_VERSION, TOOLS as SOURCE_TOOLS, phase


SCHEMA = "kit.sw2026.attached-top-box-generated.v1"
TOOLS = {*SOURCE_TOOLS, "AuthorPartProperties.py", "InspectGeneratedAttachedTopBox.py"}


def checked(root, relative, expected):
    path = (root / relative).resolve(strict=True)
    require(path.is_relative_to(root) and path.is_file() and digest(path) == expected,
            f"attached box packet identity differs: {relative}")
    return path


def read_packet(packet, expected):
    root = packet.parent
    plan = json.loads(checked(root, packet.name, expected).read_bytes())
    require(plan["schema"] == SCHEMA and re.fullmatch(r"[a-f0-9]{40}", plan["writer_revision"])
            and set(plan["tools"]) == TOOLS and plan["oracle_sha256"] == ORACLE
            and plan["oracle_file_version"] == ORACLE_VERSION
            and Path(__file__).resolve().parent == root / "Tools",
            "generated attached box packet does not bind the exact writer and oracle")
    require(plan["control_sha256"] == CONTROL, "generated box control identity differs")
    control_file = checked(root, "Control.SLDPRT", CONTROL)
    for name, checksum in plan["tools"].items():
        checked(root / "Tools", name, checksum)
    target = PureWindowsPath(plan["target"])
    require(target.drive.casefold() == "c:" and target.is_absolute() and len(target.parts) == 2
            and re.fullmatch(r"KitAttachedTopBoxGenerated[0-9]{2}", target.name),
            "choose an unused Windows-local generated box directory")
    require(re.fullmatch(r"Trial[0-9]{2}", plan["trial"]), "choose a fresh native measurement trial")
    lanes = {}
    for name, row in plan["cases"].items():
        require(re.fullmatch(r"[a-zA-Z0-9.-]+", name) and name not in (".", ".."),
                "generated box case name must be one native path segment")
        build = json.loads(checked(root, row["build"], row["build_sha256"]).read_bytes())
        model = checked(root, row["file"], row["file_sha256"])
        neutral = json.loads(checked(root, row["request"], row["request_sha256"]).read_bytes())
        output = target / name / model.name
        require(build["passed"] and build["runtime_input_file_reads"] == 0 and not build["native_acceptance"]
                and neutral["document"]["source"]["sha256"] == build["source_sha256"]
                and neutral["native_path"] == build["native_path"] == str(output)
                and neutral["attached_top"] is True and neutral["preserve_source_labels"] is True
                and build["sha256"] == row["file_sha256"] and build["bytes"] == model.stat().st_size
                and build["actual_native_support_plane"] == "Top Plane" and build["actual_native_boss_reversed"]
                and build["origin_coincidence"]["actual_owner_aliases"]
                and build["actual_native_body_label_plan"] == BODY
                and set(build["parameter_bindings"].values()) == set(PARAMETERS),
                "attached box bytes differ from the guarded source-only build")
        sizes = tuple(value / 1000 for value in build["source_dimensions_mm"])
        lanes[name] = (model, output, {
            "source_sha256": build["source_sha256"],
            "generated_sha256": build["sha256"],
            "original_m": sizes,
            "edit_m": tuple(value * factor for value, factor in zip(sizes, (1.35, 1.23, 1.5), strict=True)),
            "source_text": build["source_text"],
        })
    require(lanes and len({lane[2]["source_sha256"] for lane in lanes.values()}) == len(lanes),
            "generated attached box cases must have independent source identities")
    return plan, control_file, lanes


def run(packet, expected):
    require(os.name == "nt", "generated attached boxes must be observed in the Windows guest")
    plan, control_file, lanes = read_packet(packet, expected)
    target = Path(plan["target"])
    require(all(not Path(native).parent.exists() for _, native, _ in lanes.values()),
            "a generated candidate destination is already occupied")
    target.mkdir(exist_ok=True)
    trial = target / plan["trial"]
    trial.mkdir()
    local_control = trial / control_file.name
    copyfile(control_file, local_control)
    require(digest(local_control) == CONTROL, "the guest-local control copy changed")
    result_path = packet.parent / "Result.json"
    require(not result_path.exists(), "generated observation result is already occupied")
    result = {
        "schema": SCHEMA, "job_sha256": expected, "writer_revision": plan["writer_revision"],
        "oracle_sha256": ORACLE, "oracle_file_version": ORACLE_VERSION,
        "stage": "setup", "phases": [], "cases": {}, "passed": False,
    }
    write_json(result_path, result)

    def measure(label, function, *args, **keywords):
        result["stage"] = label
        write_json(result_path, result)
        observed = function(*args, **keywords)
        result["phases"].append({"name": label, **{k: v for k, v in observed.items() if k != "observations"}})
        write_json(result_path, result)
        require(observed["passed"], f"native attached-box phase failed: {label}")
        return observed

    with (trial / "Oracle.log").open("x", encoding="utf-8") as log, redirect_stdout(log), redirect_stderr(log):
        try:
            measure("ControlBefore", control, trial, "ControlBefore", local_control)
            for name, (model, native, case) in lanes.items():
                native = Path(native)
                native.parent.mkdir()
                copyfile(model, native)
                require(digest(native) == case["generated_sha256"], "copied generated part changed")
                authored = measure(name + "Edit", phase, native.parent, case, "Author", generated_input=native)
                reopened = measure(name + "Reopen", phase, native.parent, case, "Reopen", authored)
                require(digest(native) == case["generated_sha256"], "the original generated part was mutated")
                result["cases"][name] = {
                    **case, "saved": reopened["files"],
                    "body_count": reopened["observations"]["Original"]["solid"]["body_count"],
                    "mass_properties": {state: row["solid"]["mass"]
                                        for state, row in reopened["observations"].items()},
                }
                write_json(result_path, result)
        except Exception as error:
            result["first_failure"] = {"phase": result["stage"], "type": type(error).__name__, "error": str(error)}
        finally:
            try:
                measure("ControlAfter", control, trial, "ControlAfter", local_control)
            except Exception as error:
                result["final_control_failure"] = str(error)
    read_packet(packet, expected)
    rows = [row.get("oracle_identity", {}) for row in result["phases"]]
    identities = {(row.get("process_id"), row.get("process_creation_filetime")) for row in rows if row}
    result["controls_healthy"] = [row["passed"] for row in result["phases"]
                                  if row["name"] in ("ControlBefore", "ControlAfter")] == [True, True]
    result["distinct_processes"] = len(identities)
    result["passed"] = (len(result["cases"]) == len(lanes) and result["controls_healthy"]
                        and len(identities) == 2 * len(lanes) + 2
                        and not ({"first_failure", "final_control_failure"} & result.keys()))
    result["stage"] = "native_batch_passed" if result["passed"] else "native_batch_failed"
    write_json(result_path, result)
    print(json.dumps({key: result[key] for key in ("stage", "passed", "controls_healthy", "distinct_processes")}))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    parser = ArgumentParser(description="Observe generated attached Top boxes against native controls")
    parser.add_argument("packet", type=Path)
    parser.add_argument("sha256")
    args = parser.parse_args()
    raise SystemExit(run(args.packet.resolve(strict=True), args.sha256))
