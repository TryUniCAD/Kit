from argparse import ArgumentParser
import json
import math
import os
from pathlib import Path
from shutil import copyfileobj
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PlanarRegistryBuild import bind, file_sha, require, subtask
from PlanarRendererNativeSpec import CHILD, CONTROL, DRIVE, ENTRY, PHASES, SCHEMA, TRIALS, encoded, exact, verify


READBACK = Path(__file__).with_name("ReadPlanarRendererNative.py")


def working_paths(root, slot, original):
    return {name: Path(encoded(root.name, slot, original[name].name)) for name in ("parent", "child")}


def issue(root, slot, original, frozen, generated):
    paths = working_paths(root, slot, original)
    directory = paths["parent"].parent
    require(directory == paths["child"].parent == root / slot / "Working"
            and paths["child"].name == CHILD and not directory.exists() and not directory.is_symlink(),
            "generated lifecycle requires an unused owned native directory")
    directory.mkdir()
    for key, native in paths.items():
        with frozen[key].open("rb") as incoming, native.open("xb") as outgoing:
            copyfileobj(incoming, outgoing)
        exact(native, generated[key]["sha256"])
    return paths


def check_mass(first, second):
    return all(math.isclose(first[name], second[name], rel_tol=5e-7, abs_tol=1e-12)
               for name in ("volume", "area", "mass")) and all(
        math.isclose(left, right, rel_tol=5e-7, abs_tol=1e-12)
        for left, right in zip(first["com"], second["com"], strict=True))


def check_effective_density(initial, edited):
    return all(math.isclose(initial[role]["mass"] / initial[role]["volume"],
                            edited[role]["mass"] / edited[role]["volume"], rel_tol=5e-7)
               for role in ("mass", "child_mass"))


def saved_hashes(row):
    return {"parent": row["saved"]["parent"], "child": row["saved"]["child"]["native_sha256"]}


def saved_readback(paths, frozen, generated, prediction, host):
    files = {kind: {"file": str(path), "sha256": saved_hashes(generated)[kind]} for kind, path in paths.items()}
    payload = {"files": {"saved": files}, "prediction": prediction["edited"],
               "appearance": frozen["self_appearance"]["appearance"], "display": frozen["display"],
               "source_labels": host["stages"]["original"]["child_labels"]}
    data = json.dumps(payload, sort_keys=True, allow_nan=False, separators=(",", ":")).encode()
    result = subtask((READBACK,), data)
    require(result["pid"] != os.getpid() and not result["cad_runtime_imports"],
            "saved readback must run outside the native process boundary with no CAD imports")
    return result


def run(root, wanted):
    require(os.name == "nt" and Path(__file__).resolve() == (root / "CodeRoot" / ENTRY).resolve(),
            "native execution belongs to the pinned Windows observer")
    packet, inputs = verify(root, wanted)
    bind(root / "CodeRoot")
    from AuthorCurves import write_json
    from InspectCombinedPlanarMates import phase, signature
    from InspectSdkPlanarGroup import observe_options

    output = root / "Inspection"
    output.mkdir()
    phases, cases = {}, {}
    report = {"schema": SCHEMA, "packet_sha256": wanted, "writer_revision": packet["writer_revision"],
              "phases": phases, "cases": cases, "new_heldout_credit": 0, "public_writer_qualified": False,
              "whole_source_admitted": False, "passed": False}

    def checkpoint():
        write_json(output / "Result.json", report)

    def record(role, selected, paths, **kwargs):
        def observe(author, model, child):
            return observe_options(author, model, child, selected["options"])

        row = phase(selected, selected["case"], role, paths["parent"], paths["child"], output / role,
                    observe=observe, **kwargs)
        phases[role] = row
        require(file_sha(output / role / "Record.json") == row["record_sha256"], "the phase lost its native receipt")
        checkpoint()
        return row

    def comparison(original, generated, reopened, prediction):
        first, second, edited, saved = (original["rebuilt"], generated["rebuilt"], generated["edited"], reopened["rebuilt"])
        a, b = signature(first), signature(second)
        checks = {"source_and_generated_tree_and_owners": {name: a[name] == b[name] for name in a},
                  "authored_original_tree": first["tree"] == prediction["source_parent_tree"],
                  "persisted_source_child_stamp": original["child_stamp_on_open"] == prediction["child_update_stamp"],
                  "source_and_generated_mechanics": {name: check_mass(first[name], second[name])
                                                     for name in ("mass", "child_mass")},
                  "source_author_mass": check_mass(first["mass"], prediction["source_mass"]),
                  "edit_kept_ordered_native_tree": signature(edited) == b,
                  "edit_preserved_effective_density": check_effective_density(second, edited),
                  "reopen_kept_ordered_native_tree": signature(edited) == signature(saved),
                  "reopen_preserved_mechanics": {name: check_mass(edited[name], saved[name])
                                                for name in ("mass", "child_mass")}}
        return {**checks, "passed": all(all(value.values()) if type(value) is dict else value for value in checks.values())}

    control, control_prediction, *_ = inputs[CONTROL]
    saved_cases = {}
    try:
        before = record("ControlBefore", control_prediction["initial"], control)
        if before["passed"]:
            for slot in TRIALS:
                original, prediction, frozen, request, host = inputs[slot]
                result = cases[slot] = {"passed": False}
                try:
                    source_row = record(slot + "Original", prediction["initial"], original)
                    if not source_row["passed"]:
                        continue
                    paths = issue(root, slot, original, frozen, packet["cases"][slot]["generated"])

                    def edited_options(author, model, child):
                        return observe_options(author, model, child, prediction["edited"]["options"])

                    generated = record(slot + "Generated", prediction["initial"], paths, editing=True,
                                       child_depth_edit=(DRIVE, prediction["depth_edit_m"]), observe_edited=edited_options)
                    if not generated["passed"]:
                        continue
                    reopened = record(slot + "FreshReopen", prediction["edited"], paths, reopened=generated["saved"])
                    if reopened["passed"]:
                        saved_cases[slot] = (paths, request, generated, prediction, host)
                        result["native_comparison"] = comparison(source_row, generated, reopened, prediction)
                except Exception as error:
                    result["error"] = repr(error)
                finally:
                    checkpoint()
    finally:
        after = record("ControlAfter", control_prediction["initial"], control)
        report["controls_healthy"] = bool(phases.get("ControlBefore", {}).get("passed") and after["passed"])
        report["control_identity_preserved"] = bool(report["controls_healthy"]
            and signature(phases["ControlBefore"]["rebuilt"]) == signature(after["rebuilt"])
            and after["rebuilt"]["tree"] == control_prediction["source_parent_tree"]
            and check_mass(phases["ControlBefore"]["rebuilt"]["mass"], after["rebuilt"]["mass"]))
        checkpoint()

    for slot, job in saved_cases.items():
        result = cases[slot]
        try:
            result["saved_strict_read"] = saved_readback(*job)
            result["passed"] = bool(result["native_comparison"]["passed"] and result["saved_strict_read"]["passed"])
        except Exception as error:
            result["saved_strict_read"] = {"error": repr(error), "passed": False}
        checkpoint()
    verify(root, wanted)
    report["frozen_inputs_unchanged"] = True
    report["saved_files_unchanged"] = all(exact(job[0][name], value).is_file()
        for job in saved_cases.values() for name, value in saved_hashes(job[2]).items())
    report["native_processes"] = len({row["oracle_identity"]["process_creation_filetime"] for row in phases.values()
                                       if row.get("oracle_identity")})
    report["numeric_checks"] = sum(row["numeric_checks"] for row in phases.values())
    report["passed"] = bool(tuple(phases) == PHASES and report["native_processes"] == len(PHASES)
        and report["control_identity_preserved"] and report["saved_files_unchanged"]
        and all(row["passed"] for row in phases.values()) and all(cases[slot]["passed"] for slot in TRIALS))
    checkpoint()
    return {name: report[name] for name in ("passed", "controls_healthy", "native_processes", "numeric_checks")}


def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("verify", "run"))
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    if args.mode == "verify":
        packet, inputs = verify(args.packet, args.packet_sha256)
        report = {"passed": True, "native_processes": 0, "guarded_pairs": len(packet["cases"]),
                  "controls": [PHASES[0], PHASES[-1]], "exact_input_pairs": len(inputs)}
    else:
        report = run(args.packet, args.packet_sha256)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
