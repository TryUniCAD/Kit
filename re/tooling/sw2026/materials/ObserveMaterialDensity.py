from argparse import ArgumentParser
from pathlib import Path
from math import isclose, isfinite
import json
import os
import sys


JOB = "292df06a2fd4f740c2070a32152568271eaf1c95be2675a9564e541f4c0b677f"
PREVIOUS = "7ba51e40c30237afd87bbd61f5de1f3f676c525e53269c632f268f11d4e2addb"
SCHEMA = "kit.sw2026.named-material-density-diagnostic.v1"


def modern_mass(author):
    part = author.typed(author.model, "PartDoc")
    body, = author.get(part, "GetBodies2", 0, False)
    author.get(author.model, "ClearSelection2", True)
    try:
        if not author.get(body, "Select2", False, author.sw.nothing()):
            raise ValueError("selection refused for the actual solid")
        extension = author.get(author.model, "Extension")
        props = author.typed(author.get(extension, "CreateMassProperty2"), "MassProperty2")
        author.set(props, "UseSystemUnits", True)
        if not author.get(props, "Recalculate"):
            raise ValueError("selected body mass recalculation failed")
        fields = {name.lower(): float(author.get(props, name)) for name in ("Volume", "Mass", "Density")}
        if not all(isfinite(value) and value > 0 for value in fields.values()):
            return {"unavailable": "nonpositive mass or geometry", "observed": fields}
        fields["use_system_units"] = bool(author.get(props, "UseSystemUnits"))
        fields["derived_density"] = fields["mass"] / fields["volume"]
        return fields
    except (ValueError, TypeError, AttributeError, author.sw.pythoncom.com_error) as error:
        return {"unavailable": type(error).__name__, "detail": repr(error)}
    finally:
        author.get(author.model, "ClearSelection2", True)


def snapshot(author, case):
    from MaterialSourceFacts import effective_mass, observe

    state = observe(author, case, case["depth_m"])
    return {key: state[key] for key in ("part_material", "body_material", "body_material_id_name", "mass")} | {
        "selected_mass_property2": modern_mass(author), "legacy_after": effective_mass(author),
    }


def phase(folder, case, material, candidate, *, reopen):
    from AuthorAssignedMaterials import save
    from AuthorCurves import Recorder, digest, require
    from AuthorRectangleAnchors import ORACLE, RectangleAuthor
    from MaterialSourceFacts import apply_material, compare_identity
    from OracleIdentity import application_identity
    import Swapp

    stage = "Reopen" if reopen else "Author"
    directory = folder / stage
    directory.mkdir(exist_ok=False)
    recorder = Recorder(directory / "Record.json", {"phase": stage, "material_source_only": True})
    result = {"passed": False, "states": {}}
    recorder.data["result"] = result
    before_hash = digest(candidate) if reopen else None
    controller = author = None
    with Swapp.Dismisser() as dialogs:
        try:
            recorder.call("guard the idle native oracle", Swapp.sweep)
            controller = recorder.call("start a fresh material oracle", Swapp.Sw)
            identity = recorder.call("bind exact oracle", application_identity, controller.app)
            require(identity["sha256"] == ORACLE and identity["version_matches"]
                    and controller.revision == "34.5.2", "material oracle identity differs")
            result["identity"] = identity
            author = RectangleAuthor(controller.app, recorder, Swapp)
            if reopen:
                author.model, errors, warnings = controller.open(candidate, read_only=True)
                require(author.model is not None and errors == warnings == 0
                        and Path(author.get(author.model, "GetPathName")).samefile(candidate),
                        "exact diagnostic reopen failed")
                result["states"]["reopened"] = snapshot(author, case)
                require(author.get(author.model, "ForceRebuild3", False), "diagnostic rebuild failed")
            else:
                author.build(controller, case)
                result["states"]["unassigned"] = snapshot(author, case)
                require(not result["states"]["unassigned"]["part_material"]["material"], "unexpected initial material")
                apply_material(author, material, case["configuration"])
            result["states"]["assigned"] = snapshot(author, case)
            compare_identity(author, result["states"]["assigned"]["part_material"], material)
            if not reopen:
                result["file"] = save(author, controller, candidate)
                result["states"]["saved"] = snapshot(author, case)
                compare_identity(author, result["states"]["saved"]["part_material"], material)
            else:
                require(digest(candidate) == before_hash, "read-only material observation changed the file")
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
        finally:
            if controller is not None:
                try:
                    if author is not None and author.model is not None:
                        controller.close_doc(author.model)
                    controller.close()
                    Swapp.sweep()
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    result["passed"] &= not bool(dialogs.log or recorder.data["first_failure"]
                                 or recorder.data["cleanup_errors"] or result.get("controller_diagnostics"))
    result["dialogs"] = dialogs.log
    recorder.data["passed"] = result["passed"]
    recorder.flush()
    return result | {"record_sha256": digest(recorder.path)}


def main():
    parser = ArgumentParser(description="Compare part density before and after native save and fresh reopen")
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--tool-sha256", required=True)
    args = parser.parse_args()
    if os.name != "nt":
        raise ValueError("use the root Windows oracle")
    sys.path.insert(0, str(args.original.parent.resolve(strict=True) / "Tools"))
    from AuthorAssignedMaterials import verify
    from AuthorCurves import digest, require, write_json
    from AuthorRectangleAnchors import control

    require(digest(Path(__file__)) == args.tool_sha256, "diagnostic observer changed")
    root, job, seed = verify(args.original, JOB, runtime=True)
    old = root / "Inspection" / "Result.json"
    require(digest(old) == PREVIOUS, "frozen failed original observation changed")
    case = job["cases"][0]
    material = job["materials"][case["first_material_key"]]
    output = Path(__file__).resolve().parent / "Native"
    output.mkdir(exist_ok=False)
    candidate = output / "AssignedDensityProbe.SLDPRT"
    rows = {}
    try:
        rows["Before"] = control(output, "Before", seed)
        if rows["Before"]["passed"]:
            rows["Author"] = phase(output, case, material, candidate, reopen=False)
            if rows["Author"]["passed"]:
                rows["Reopen"] = phase(output, case, material, candidate, reopen=True)
    finally:
        rows["After"] = control(output, "After", seed)
    verify(args.original, JOB, runtime=True)
    controls = rows["Before"]["passed"] and rows["After"]["passed"]
    identities = tuple(row.get("identity", row.get("oracle_identity")) for row in rows.values())
    processes = {(row["process_id"], row["process_creation_filetime"]) for row in identities if row is not None}
    complete = controls and len(processes) == len(rows) == 4 and all(row["passed"] for row in rows.values())
    observations = [row["states"]["assigned"] for row in rows.values() if "assigned" in row.get("states", {})]
    hypothesis = material["density_si_hypothesis"]
    matches = complete and len(observations) == 2 and all(
        isclose(row["mass"]["density"], hypothesis, rel_tol=5e-7)
        and isclose(row["selected_mass_property2"].get("density", -1.0), hypothesis, rel_tol=5e-7)
        for row in observations
    )
    result = {"schema": SCHEMA, "complete_observations": complete, "controls_healthy": controls,
              "observed_density_hypothesis": matches, "distinct_native_processes": len(processes),
              "previous_result_sha256": PREVIOUS, "packet_sha256": JOB, "tool_sha256": args.tool_sha256,
              "rows": rows, "source_lifecycle_qualified": False, "sealed_originals_locked": False}
    write_json(output / "Result.json", result)
    print(json.dumps({"complete_observations": complete, "density_hypothesis": matches,
                      "processes": len(processes), "result_sha256": digest(output / "Result.json")}))
    return int(not complete)


if __name__ == "__main__":
    sys.exit(main())
