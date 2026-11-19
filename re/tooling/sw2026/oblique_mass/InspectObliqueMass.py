import argparse
from hashlib import sha256
import json
import os
from pathlib import Path, PureWindowsPath
import shutil
import time

from ObliqueMass import binding, collect, require

SCHEMA = "kit.sw2026.oblique-mass-diagnostic.v1"
BASELINE = "0cc67981af46bcee916354bdf90b7204c9a6bf74d89fb8104636e2728c3034d8"
REGISTRY = "ae1cb6e0fd42acc1ca2988582af2374ef9519bae3cd868f80724ad84c145b99a"
PHASES = ("ControlBefore", "F01", "F02", "ControlAfter")


def fingerprint(path):
    return sha256(path.read_bytes()).hexdigest()


def store(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def prepare(args):
    source, target = args.baseline.resolve(), args.output.resolve()
    require(
        not target.exists() and target.parent.is_dir(),
        "use an unused diagnostic packet",
    )
    require(
        fingerprint(source / "Protocol.json") == BASELINE
        and fingerprint(args.mass_metadata) == REGISTRY,
        "diagnostic source identity differs",
    )
    previous = json.loads((source / "Protocol.json").read_bytes())
    require(
        previous["writer_output_count"] == 0
        and previous["heldout_execution_enabled"] is False,
        "only the disclosed source profile is admitted",
    )
    target.mkdir()
    (target / "Tools").mkdir()
    for name in previous["tools_sha256"]:
        require(
            fingerprint(source / "Tools" / name) == previous["tools_sha256"][name],
            "frozen source tool differs",
        )
        shutil.copyfile(source / "Tools" / name, target / "Tools" / name)
    shutil.copyfile(source / "Protocol.json", target / "BaselineProtocol.json")
    for name in (
        "Disclosed.json",
        "Predictions.json",
        "Control.SLDPRT",
        "ApiMetadata.json",
    ):
        shutil.copyfile(source / name, target / name)
    shutil.copyfile(args.mass_metadata, target / "MassApi.json")
    for name in ("ObliqueMass.py", "InspectObliqueMass.py"):
        shutil.copyfile(Path(__file__).parent / name, target / "Tools" / name)
    binding(json.loads((target / "MassApi.json").read_bytes()))
    files = {
        name: fingerprint(target / name)
        for name in (
            "BaselineProtocol.json",
            "Disclosed.json",
            "Predictions.json",
            "Control.SLDPRT",
            "ApiMetadata.json",
            "MassApi.json",
        )
    }
    tools = {
        path.name: fingerprint(path) for path in sorted((target / "Tools").glob("*.py"))
    }
    job = {
        "schema": SCHEMA,
        "baseline_sha256": BASELINE,
        "registry_sha256": REGISTRY,
        "phases": list(PHASES),
        "files_sha256": files,
        "tools_sha256": tools,
        "geometry_and_predictions_unchanged": True,
        "save_enabled": False,
        "edit_enabled": False,
        "native_acceptance": False,
        "writer_output_count": 0,
        "heldout_reads": 0,
    }
    store(target / "Trial.json", job)
    digest = fingerprint(target / "Trial.json")
    guest, python = PureWindowsPath(args.guest_root), PureWindowsPath(args.guest_python)
    require(guest.is_absolute() and python.is_absolute(), "use absolute guest paths")
    command = [str(python), "-B", str(guest / "Tools/InspectObliqueMass.py")]
    tail = [str(guest / "Trial.json"), "--packet-sha256", digest]
    commands = [{"name": "verify", "argv": command + ["verify"] + tail}]
    commands.extend(
        {"name": phase, "argv": command + ["phase"] + tail + ["--phase", phase]}
        for phase in PHASES
    )
    commands.append({"name": "summary", "argv": command + ["summary"] + tail})
    store(
        target / "Recipe.json",
        {
            "schema": SCHEMA,
            "packet_sha256": digest,
            "commands": commands,
            "always_run_ControlAfter_after_failure": True,
            "root_only_serial_execution": True,
        },
    )
    return {
        "passed": True,
        "packet_sha256": digest,
        "recipe_sha256": fingerprint(target / "Recipe.json"),
        "native_launches": 0,
    }


def verify(path, expected):
    root = path.resolve().parent
    require(
        fingerprint(path) == expected
        and Path(__file__).resolve().parent == root / "Tools",
        "diagnostic packet custody differs",
    )
    job = json.loads(path.read_bytes())
    require(
        job["schema"] == SCHEMA
        and job["baseline_sha256"] == BASELINE
        and job["registry_sha256"] == REGISTRY
        and job["phases"] == list(PHASES),
        "diagnostic profile differs",
    )
    require(
        job["geometry_and_predictions_unchanged"]
        and not job["save_enabled"]
        and not job["edit_enabled"]
        and not job["native_acceptance"]
        and job["writer_output_count"] == job["heldout_reads"] == 0,
        "diagnostic scope differs",
    )
    for name, value in job["files_sha256"].items():
        require(fingerprint(root / name) == value, "diagnostic input changed: " + name)
    for name, value in job["tools_sha256"].items():
        require(
            fingerprint(root / "Tools" / name) == value,
            "diagnostic tool changed: " + name,
        )
    from ObliqueFlipSources import verify as original_verify

    original_verify(root / "BaselineProtocol.json", BASELINE)
    metadata = json.loads((root / "MassApi.json").read_bytes())
    return root, job, binding(metadata)


def control_valid(result, sample):
    from InspectFresh import healthy

    return (
        healthy(result)
        and sample["diagnostic_complete"]
        and all(
            item["within_original_tolerance"]
            for row in (*sample["levels"], *sample["body_measurements"])
            for item in row["versus_original_default"]
        )
    )


def phase(root, job, name):
    require(os.name == "nt", "native mass diagnosis requires the guest")
    import Swapp
    import AuthorCurves as curves
    from AuthorObliqueFlip import ObliqueFlipAuthor
    from ObliqueFlipPlan import cases
    from OracleIdentity import application_identity

    if name in ("F01", "F02"):
        before = json.loads(
            (root / "Inspection/ControlBefore/Result.json").read_bytes()
        )
        require(
            before["controls_healthy"] and before["diagnostic_complete"],
            "control must qualify the new mass binding first",
        )
    directory = root / "Inspection" / name
    directory.mkdir(parents=True, exist_ok=False)
    rec = curves.Recorder(
        directory / "Record.json",
        {
            "phase": name,
            "scope": "read-only measurement of disclosed source construction; no acceptance",
        },
    )
    result = {
        "phase": name,
        "started_at": time.time(),
        "diagnostic_complete": False,
        "controls_healthy": False,
        "native_acceptance": False,
        "writer_output_count": 0,
        "heldout_reads": 0,
    }
    controller = author = None
    metadata = json.loads((root / "MassApi.json").read_bytes())
    api = json.loads((root / "ApiMetadata.json").read_bytes())
    predictions = json.loads((root / "Predictions.json").read_bytes())["cases"]
    with Swapp.Dismisser() as dialogs:
        try:
            rec.call("mass diagnostic idle guard", Swapp.sweep)
            controller = rec.call("start fresh mass diagnostic", Swapp.Sw, visible=True)
            identity = rec.call(
                "verify exact mass oracle", application_identity, controller.app
            )
            result["oracle_identity"] = identity
            require(
                identity["version_matches"]
                and identity["sha256"]
                == "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
                and controller.revision == "34.5.2",
                "oracle identity differs",
            )
            control = name.startswith("Control")
            target = predictions["F01" if control else name]
            author = ObliqueFlipAuthor(controller.app, rec, Swapp, api, target)
            if control:
                author.model, errors, warnings = rec.call(
                    "open exact control part",
                    controller.open,
                    root / "Control.SLDPRT",
                    read_only=True,
                )
                require(
                    author.model is not None and errors == warnings == 0,
                    "control did not open cleanly",
                )
                rebuilt = bool(author.get(author.model, "ForceRebuild3", False))
                features = rec.call(
                    "capture actual control history", Swapp.features, author.model
                )
                original_default = rec.call(
                    "unchanged original default mass", Swapp.mass, author.model
                )
                part = author.declared_interface(author.model, "IPartDoc")
                body_count = len(author.get(part, "GetBodies2", 0, False) or ())
                native = {
                    "opened": True,
                    "rebuilt": rebuilt,
                    "bodies": body_count,
                    "mass": original_default,
                    "open_errors": errors,
                    "open_warnings": warnings,
                    "whats_wrong": author.get(
                        author.get(author.model, "Extension"), "GetWhatsWrongCount"
                    ),
                    "features": features,
                }
                result["control"] = native
                sample = collect(author, metadata, original_default)
                result["controls_healthy"] = control_valid(native, sample)
            else:
                (case,) = [value for value in cases() if value["id"] == name]
                author.build(case, controller)
                observed = None
                try:
                    observed = author.snapshot(case, 0)
                    result["original_analytic_comparison_passed"] = True
                except Exception as error:
                    rec.failure(error)
                    result["original_analytic_comparison_passed"] = False
                    result["preserved_original_failure"] = repr(error)
                    observed = rec.data.get("partial_oblique_snapshot")
                require(
                    observed is not None
                    and observed.get("body_count") == 1
                    and observed.get("mass")
                    and "error" not in observed["mass"],
                    "original observation did not reach measurable single-body geometry",
                )
                analytic = target["0"]
                sample = collect(
                    author,
                    metadata,
                    observed["mass"],
                    {
                        "volume": analytic["volume_m3"],
                        "area": analytic["area_m2"],
                        "com": analytic["com_m"],
                    },
                )
            result["mass_precision"] = sample
            result["diagnostic_complete"] = sample["diagnostic_complete"] and (
                not control or result["controls_healthy"]
            )
        except Exception as error:
            rec.failure(error)
            result["diagnostic_error"] = repr(error)
        finally:
            if author is not None and author.model is not None:
                try:
                    rec.call(
                        "close owned diagnostic part without save",
                        controller.close_doc,
                        author.model,
                    )
                except Exception as error:
                    rec.failure(error, cleanup=True)
            if controller is not None:
                try:
                    controller.close()
                except Exception as error:
                    rec.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    result["dialogs"] = dialogs.log
    result["finished_at"] = time.time()
    result["diagnostic_complete"] = bool(
        result["diagnostic_complete"]
        and not dialogs.log
        and not result.get("controller_diagnostics")
        and not rec.data["cleanup_errors"]
    )
    result["controls_healthy"] = bool(
        result["controls_healthy"] and result["diagnostic_complete"]
    )
    rec.data.update(result=result, finished_at=result["finished_at"])
    rec.flush()
    result["record_sha256"] = fingerprint(directory / "Record.json")
    store(directory / "Result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "verify", "phase", "summary"))
    parser.add_argument("packet", type=Path, nargs="?")
    parser.add_argument("--packet-sha256")
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--mass-metadata", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--guest-root")
    parser.add_argument("--guest-python")
    parser.add_argument("--phase", choices=PHASES)
    args = parser.parse_args()
    if args.mode == "prepare":
        result = prepare(args)
    else:
        root, job, plan = verify(args.packet, args.packet_sha256)
        if args.mode == "verify":
            result = {"passed": True, "native_launches": 0, "binding": plan}
        elif args.mode == "phase":
            result = phase(root, job, args.phase)
            verify(args.packet, args.packet_sha256)
        else:
            rows = [
                json.loads((root / "Inspection" / name / "Result.json").read_bytes())
                for name in PHASES
            ]
            births = [
                value.get("oracle_identity", {}).get("process_creation_filetime")
                for value in rows
            ]
            controls = rows[0]["controls_healthy"] and rows[-1]["controls_healthy"]
            complete = (
                controls
                and all(value["diagnostic_complete"] for value in rows)
                and None not in births
                and len(set(births)) == 4
            )
            result = {
                "diagnostic_complete": complete,
                "controls_healthy": controls,
                "distinct_native_processes": len(set(births) - {None}),
                "preserved_original_comparisons": {
                    row["phase"]: row.get("original_analytic_comparison_passed")
                    for row in rows[1:3]
                },
                "result_sha256": {
                    name: fingerprint(root / "Inspection" / name / "Result.json")
                    for name in PHASES
                },
                "native_acceptance": False,
                "writer_output_count": 0,
                "heldout_reads": 0,
            }
            store(root / "Inspection/Result.json", result)
    printed = {
        key: result[key]
        for key in (
            "passed",
            "diagnostic_complete",
            "controls_healthy",
            "packet_sha256",
            "recipe_sha256",
            "native_launches",
            "native_acceptance",
            "original_analytic_comparison_passed",
        )
        if key in result
    }
    print(json.dumps(printed))
    return 0 if result.get("passed", result.get("diagnostic_complete", False)) else 3


if __name__ == "__main__":
    raise SystemExit(main())
