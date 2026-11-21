from argparse import ArgumentParser
from math import isclose
from pathlib import Path
import json
import os

from AuthorCurves import Recorder, digest, require, write_json
from AuthorRectangleAnchors import ORACLE, RectangleAuthor, control
from MaterialSourceFacts import effective_mass, material_identity, selected_mass
from OracleIdentity import application_identity
import Swapp

MODES = ("unassigned", "part", "configuration", "identity", "all")


def read_job(job_path, pin):
    require(os.name == "nt" and job_path.is_absolute() and digest(job_path) == pin,
            "exact Windows-local probe job required")
    job = json.loads(job_path.read_bytes())
    root = job_path.parent.resolve()
    require(job_path.name == "Job.json" and str(root) == job["guest_root"] and root.drive == "C:",
            "probe must use its declared local candidate directory")
    require(job["schema"] == "kit.sw2026.assigned-material-probe-job.v1" and job["oracle_sha256"] == ORACLE,
            "probe method or exact native build differs")
    allow = {"Tools", "Models", "Control.SLDPRT", "Job.json", "Inspection"}
    require({p.name for p in root.iterdir()} <= allow, "unplanned input in the native probe packet")
    require(set(job["tools_sha256"]) == {p.name for p in (root / "Tools").iterdir() if p.is_file()},
            "native probe tool inventory differs")
    for name, expected in job["tools_sha256"].items():
        require(Path(name).name == name and digest(root / "Tools" / name) == expected, "probe tool changed: " + name)
    control = root / "Control.SLDPRT"
    require(digest(control) == job["control_sha256"], "known control changed")
    require(set(job["cases"]) == {p.stem for p in (root / "Models").iterdir() if p.is_file()},
            "unguarded candidate in native probe packet")
    require(tuple(job["cases"][key]["mode"] for key in job["order"]) == (*MODES, "all"),
            "the five physical contrasts and independent second-material case must be ordered")
    for key, row in job["cases"].items():
        candidate = root / "Models" / (key + ".SLDPRT")
        require(digest(candidate) == row["sha256"] and candidate.stat().st_size == row["bytes"],
                "generated candidate custody changed: " + key)
    return root, job, control


def snapshot(author, row, label):
    part = author.typed(author.model, "PartDoc")
    config = author.get(author.get(author.model, "ConfigurationManager"), "ActiveConfiguration")
    name = author.get(config, "Name")
    require(name == row["configuration"], "candidate active configuration is wrong")
    bodies = tuple(author.get(part, "GetBodies2", 0, False) or ())
    shown = tuple(author.get(part, "GetBodies2", 0, True) or ())
    require(len(bodies) == len(shown) == 1, "candidate must load one actual visible solid")
    body = author.typed(bodies[0], "Body2")
    volume, area, center = (row["geometry"][key] for key in ("volume", "area", "com"))
    measured = effective_mass(author)
    scoped = selected_mass(author, body)
    author.rec.close_number(label + " prism volume", measured["volume"], volume, absolute=1e-16)
    author.rec.close_number(label + " selected prism volume", scoped["volume"], volume, absolute=1e-16)
    author.rec.close_number(label + " prism area", measured["area"], area, absolute=1e-12)
    for observed, expected in zip(measured["com"], center, strict=True):
        author.rec.close_number(label + " prism centroid", observed, expected)
    author.rec.close_number(label + " density consistency", scoped["mass_over_volume_density"], scoped["density"])
    tree = author.feature_tree(required_names=tuple(row["feature_names"]))
    drivers = {}
    for key, value in row["drivers_m"].items():
        dimension = author.get(author.model, "Parameter", key)
        require(dimension is not None and author.get(dimension, "DrivenState") == 2
                and not author.get(dimension, "ReadOnly"), "generated dimension is not native editable: " + key)
        drivers[key] = float(author.get(dimension, "SystemValue"))
        author.rec.close_number(label + " live dimension " + key, drivers[key], value)
    identity = material_identity(author, part, "GetMaterialPropertyName2", name)
    actual_catalog = Path(identity["database"]).stem.casefold()
    density = row["density_kg_m3"]
    return {"body_count": len(bodies), "material": identity,
            "body_id_name": author.get(body, "GetMaterialIdName2"), "drivers_m": drivers,
            "matches_requested_identity": identity["material"] == row["material"]
            and actual_catalog == row["catalog"].casefold(),
            "matches_requested_density": isclose(scoped["density"], density, rel_tol=5e-7),
            "matches_requested_mass": isclose(scoped["mass"], density * volume, rel_tol=5e-7),
            "mass_properties": measured, "selected_mass_properties": scoped, "tree": tree}


def inspect(output, candidate, row):
    output.mkdir(exist_ok=False)
    rec = Recorder(output / "Record.json", {"phase": "generated_material_probe", "mode": row["mode"]})
    report = {"passed": False, "identity": None, "snapshots": {}, "open_errors_warnings": None}
    rec.data["result"] = report
    controller = author = None
    with Swapp.Dismisser() as dialogs:
        try:
            require(not Swapp.application_pids(), "the named oracle must already be idle")
            controller = rec.call("start fresh generated probe oracle", Swapp.Sw)
            report["identity"] = application_identity(controller.app)
            require(report["identity"]["sha256"] == ORACLE and report["identity"]["version_matches"]
                    and controller.revision == "34.5.2", "generated probe opened in wrong licensed build")
            author = RectangleAuthor(controller.app, rec, Swapp)
            author.model, errors, warnings = rec.call("open generated probe read-only", controller.open,
                                                       candidate, read_only=True)
            report["open_errors_warnings"] = [errors, warnings]
            require(author.model is not None and errors == warnings == 0
                    and Path(author.get(author.model, "GetPathName")).samefile(candidate),
                    "generated probe failed to open cleanly at the exact locator")
            report["snapshots"]["cold"] = snapshot(author, row, "cold")
            require(author.get(author.model, "ForceRebuild3", False)
                    and author.get(author.get(author.model, "Extension"), "GetWhatsWrongCount") == 0,
                    "generated probe rebuild failed or reported warnings")
            report["snapshots"]["rebuilt"] = snapshot(author, row, "rebuilt")
            report["passed"] = True
        except Exception as error:
            rec.failure(error)
            report["error"] = repr(error)
        finally:
            if controller is not None:
                try:
                    if author is not None and author.model is not None:
                        controller.close_doc(author.model)
                    controller.close()
                    require(not Swapp.application_pids(), "generated probe process did not exit")
                except Exception as error:
                    rec.failure(error, cleanup=True)
                report["controller_diagnostics"] = controller.diagnostics
    report.update(dialogs=dialogs.log, numeric_checks=len(rec.data["checks"]),
                  artifact_sha256=digest(candidate))
    report["passed"] = bool(report["passed"] and report["artifact_sha256"] == row["sha256"]
                            and not dialogs.log and not rec.data["cleanup_errors"]
                            and not report["controller_diagnostics"])
    rec.data["passed"] = report["passed"]
    rec.flush()
    return report | {"record_sha256": digest(rec.path)}


def run(path, pin):
    root, job, seed = read_job(path, pin)
    output = root / "Inspection"
    output.mkdir(exist_ok=False)
    report = {"schema": "kit.sw2026.assigned-material-probe-native.v1", "job_sha256": pin,
              "cold_rebuild_only": True, "heldout_credit": 0, "product_acceptance": False, "cases": {}}
    result_path = output / "Result.json"
    try:
        report["control_before"] = control(output, "ControlBefore", seed)
        if report["control_before"]["passed"]:
            for name in job["order"]:
                candidate = root / "Models" / (name + ".SLDPRT")
                report["cases"][name] = inspect(output / name, candidate, job["cases"][name])
                write_json(result_path, report)
    finally:
        report["control_after"] = control(output, "ControlAfter", seed)
        rows = [report.get("control_before", {}), report["control_after"], *report["cases"].values()]
        identities = (row.get("identity") or row.get("oracle_identity") for row in rows)
        report["distinct_processes"] = len({(i["process_id"], i["process_creation_filetime"]) for i in identities if i})
        report["controls_healthy"] = all(report.get(key, {}).get("passed", False)
                                         for key in ("control_before", "control_after"))
        report["observations_complete"] = (report["controls_healthy"]
                                           and len(rows) == report["distinct_processes"] == len(job["order"]) + 2)
        read_job(path, pin)
        write_json(result_path, report)
    return {"result_sha256": digest(result_path), "complete": report["observations_complete"],
            "controls_healthy": report["controls_healthy"], "native_processes": report["distinct_processes"],
            "loaded_and_rebuilt": sum(row["passed"] for row in report["cases"].values())}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--job", required=True, type=Path)
    parser.add_argument("--pin", required=True)
    args = parser.parse_args()
    result = run(args.job, args.pin)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(not result["complete"])
