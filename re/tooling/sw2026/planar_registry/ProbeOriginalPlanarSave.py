from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from shutil import copyfileobj
import json
import os
import sys


PACKET_PIN = "a8776d5de20ee7c691cb088a5bb589944ef0c24bf7e57b908b7d088177be989c"
RESULT_PIN = "215f24271caf6c3289cc56ae12f4f8e02b45d98b01329ec61b309a16b7b184e1"
SCHEMA = "kit.sw2026.original-planar-renderer-resave.v1"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run(earlier, output, tool_pin):
    assert os.name == "nt" and digest(Path(__file__)) == tool_pin
    assert output.parent == earlier.parent and not output.exists()
    assert digest(earlier / "Inspection" / "Result.json") == RESULT_PIN
    prior = json.loads((earlier / "Inspection" / "Result.json").read_bytes())
    assert prior["controls_healthy"] and prior["saved_files_unchanged"]
    assert all(row["native_comparison"]["passed"] for row in prior["cases"].values())
    root = earlier / "CodeRoot"
    sys.path[:0] = [str(root / "re/tooling/sw2026/planar_registry"), str(root / "re/tooling/sw2026")]
    from PlanarRegistryBuild import bind
    from PlanarRendererNativeSpec import CONTROL, DRIVE, TRIALS, exact, verify

    _, cases = verify(earlier, PACKET_PIN)
    bind(root)
    import Swapp
    from AuthorCurves import write_json
    from InspectCombinedPlanarMates import phase, signature
    from InspectSdkPlanarGroup import observe_options
    from ObservePlanarRendererNative import check_effective_density, check_mass
    from PlanarRendererInput import material_id, observe_looks
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from para.concentric.ProveVisualStateStore import registry

    output.mkdir()
    raw_checks = output / "Phases"
    raw_checks.mkdir()
    result = {"schema": SCHEMA, "previous_packet_sha256": PACKET_PIN, "previous_result_sha256": RESULT_PIN,
              "method_sha256": tool_pin, "cases": {}, "controls": {}, "writer_output_count": 0,
              "heldout_credit": 0, "full_assembly_qualified": False, "passed": False}
    identities = []
    observed = {}
    control, reference, *_ = cases[CONTROL]

    def inspect(label, prediction, paths, **extra):
        assert not Swapp.application_pids() and not Swapp.owned_process_ids()
        options = prediction["options"]
        def observe(author, model, child):
            return observe_options(author, model, child, options)
        outcome = phase(prediction, prediction["case"], label, paths["parent"], paths["child"],
                        raw_checks / label, observe=observe, **extra)
        if "oracle_identity" in outcome:
            identities.append(outcome["oracle_identity"]["process_creation_filetime"])
        if outcome["passed"]:
            assert digest(raw_checks / label / "Record.json") == outcome["record_sha256"]
        observed[label] = outcome
        return outcome

    def material_roles(path):
        archive = SldprtArchive.from_bytes(path.read_bytes(), path.name)
        owners, manager, view = observe_looks(archive, registry())
        return {"appearance_ids": list(map(material_id, owners)),
                "definition_cursor": manager.AppearanceValue.NextAppearanceId,
                "child_view_sha256": view["sha256"],
                "density": view["physical_density_parameter"],
                "selected_density": view["active_configuration_density"]}

    original_locks = {key: {role: digest(path) for role, path in files.items()}
                      for key, (files, *_) in cases.items()}
    try:
        before = inspect("ControlBefore", reference["initial"], control)
        if before["passed"]:
            for trial in TRIALS:
                files, expected, *_ = cases[trial]
                working = output / trial
                working.mkdir()
                paths = {role: working / files[role].name for role in ("parent", "child")}
                for role, path in paths.items():
                    source = exact(files[role], original_locks[trial][role])
                    with source.open("rb") as incoming, path.open("xb") as outgoing:
                        copyfileobj(incoming, outgoing)
                    exact(path, original_locks[trial][role])
                row = result["cases"][trial] = {"passed": False}
                def after_edit(author, model, child):
                    return observe_options(author, model, child, expected["edited"]["options"])
                edited = inspect(trial + "EditableOriginal", expected["initial"], paths, editing=True,
                                 child_depth_edit=(DRIVE, expected["depth_edit_m"]), observe_edited=after_edit)
                row["edited_phase_sha256"] = edited["record_sha256"]
                if not edited["passed"]:
                    row["first_failure"] = "native original edit did not complete on the owned copies"
                    continue
                fresh = inspect(trial + "FreshReopen", expected["edited"], paths, reopened=edited["saved"])
                row["reopen_phase_sha256"] = fresh["record_sha256"]
                if not fresh["passed"]:
                    row["first_failure"] = "edited original copy did not reopen with a synchronized child"
                    continue
                initial, a, b = edited["rebuilt"], edited["edited"], fresh["rebuilt"]
                counterpart = prior["phases"][trial + "FreshReopen"]["rebuilt"]
                row.update(ordered_tree_matches=signature(initial) == signature(a) == signature(b) == signature(counterpart),
                           mechanics_match=all(check_mass(a[name], b[name]) and check_mass(b[name], counterpart[name])
                                               for name in ("mass", "child_mass")),
                           preserves_effective_density=check_effective_density(initial, a),
                           original_roles=material_roles(files["child"]), resaved_roles=material_roles(paths["child"]),
                           saved_parent_sha256=digest(paths["parent"]), saved_child_sha256=digest(paths["child"]))
                row["passed"] = row["ordered_tree_matches"] and row["mechanics_match"] and row["preserves_effective_density"]
    except Exception as error:
        result["failure_type"] = type(error).__name__
    finally:
        inspect("ControlAfter", reference["initial"], control)
        result["controls"] = {key: {"passed": observed[key]["passed"], "phase_sha256": observed[key]["record_sha256"]}
                              for key in ("ControlBefore", "ControlAfter")}
    result["originals_unchanged"] = all(digest(path) == original_locks[key][role]
                                         for key, (files, *_) in cases.items() for role, path in files.items())
    result["native_processes"] = len(set(identities))
    result["numeric_checks"] = sum(row["numeric_checks"] for row in observed.values())
    controls_match = all(row["passed"] for row in result["controls"].values())
    if controls_match:
        first, last = (observed[label]["rebuilt"] for label in ("ControlBefore", "ControlAfter"))
        controls_match = (signature(first) == signature(last) and last["tree"] == reference["source_parent_tree"]
                          and all(check_mass(first[name], last[name]) for name in ("mass", "child_mass")))
    result["controls_match"] = controls_match
    result["passed"] = (not result.get("failure_type") and result["originals_unchanged"]
                        and len(identities) == result["native_processes"] == 6
                        and len(result["cases"]) == 2 and all(row["passed"] for row in result["cases"].values())
                        and controls_match)
    destination = output / "Receipt.json"
    write_json(destination, result)
    print(json.dumps({key: result[key] for key in ("passed", "native_processes", "numeric_checks")} |
                     {"receipt_sha256": digest(destination)}))
    return int(not result["passed"])


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("earlier", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--tool-pin", required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.earlier, args.output, args.tool_pin))
