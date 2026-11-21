import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from NativeAcceptance.Availability import ApiStatus
from NativeAcceptance.Assessment import AssessChecks
from NativeAcceptance.CompareDocument import CompareDocument, NumericEqual, SameValues
from NativeAcceptance.Records import Endpoint, FileHash, ReadBytes, WriteJson
from NativeAcceptance.RunCase import RunCase


def ReadControl(root, application):
    if application == "solidworks":
        relative = "re/automation/PairedCaptures/P03/solidworks-db1390476325/P03-solidworks-baseline-a.SLDPRT"
        expected = "db1390476325f5817e6f80fb4067a3c6df5cc063315604c133ccbeaafdeac357"
    else:
        relative = "re/automation/PairedCaptures/P03/fusion-8d53584027ff/P03-fusion-baseline-a.f3d"
        expected = "9f109b98ab7d36abeda8d9f88f9b336277238ce0bb3336d99313253ad47b2745"
    data = subprocess.run(["git", "--no-replace-objects", "-C", str(root), "show", "HEAD:" + relative], check=True, capture_output=True, timeout=15).stdout
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("native healthy control differs from its reviewed research pin")
    return data


def CheckMeasurement(result):
    if result.get("status") != "measured" or result.get("load_errors") or result.get("documents_after") != 0:
        return False
    rebuilt = result["rebuilt"]
    import math

    return bool(rebuilt["bodies"] and rebuilt["features"]) and SameValues(result.get("opened"), rebuilt) and all(math.isfinite(item["volume_mm3"]) and item["volume_mm3"] > 0 and len(item["center_mm"]) == 3 and all(math.isfinite(value) for value in item["center_mm"]) for item in rebuilt["bodies"]) and all(not item["health"] and not item["message"] for item in rebuilt["features"])


def MeasureFile(application, availability, payload, suffix, role, configuration=None):
    parent = Endpoint() / "jobs" if application == "fusion" else None
    if parent is not None:
        parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        if any(not (path.parent / "response.json").is_file() for path in parent.glob("*/request.json")):
            raise ValueError("a previous Fusion verification request needs owner recovery before another native batch")
    work = Path(tempfile.mkdtemp(prefix="case-", dir=parent))
    source = work / ("source" + suffix)
    try:
        source.write_bytes(payload)
        result = RunCase(application, work, source, role, availability, configuration)
        yield work, result
    finally:
        if not (work / "request.json").exists() or (work / "response.json").exists():
            shutil.rmtree(work)


def HealthyControl(result):
    return CheckMeasurement(result) and len(result["rebuilt"]["bodies"]) == 1 and NumericEqual(result["rebuilt"]["bodies"][0]["volume_mm3"], 8000.0) and SameValues(result["rebuilt"]["bodies"][0]["center_mm"], [20.0, 10.0, 5.0])


def VerifyBatch(root, application, samples, output):
    from contextlib import closing
    from convert import open_document

    availability = ApiStatus(application)
    revision = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=15, check=True).stdout.strip()
    report = {"schema": 1, "application": application, "source_revision": revision, "scope": "native_source_reader_verification", "status": "unverified", "portable_complete": False, "conversion_qualified": False, "live_batch_verified": False, "full_semantics_verified": False, "semantic_gaps": ["complete_feature_definitions", "constraint_operands", "reference_bindings"], "cases": [], "controls": {}}
    if availability["status"] != "available":
        report.update(status="api_unavailable", action=availability["action"])
        WriteJson(output, report)
        return report
    source_format = "solidworks.sldprt" if application == "solidworks" else "fusion.f3d"
    suffix = ".SLDPRT" if application == "solidworks" else ".f3d"
    control = ReadControl(root, application)
    sources = {str(path): FileHash(path) for base in (root / "src", root / "re/automation/NativeAcceptance") for path in base.rglob("*.py")}
    report["source_inventory_sha256"] = hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()
    process_ids = set()
    build = None
    try:
        with closing(MeasureFile(application, availability, control, suffix, "control")) as measurement:
            _, before = next(measurement)
            report["controls"]["before"] = before
        if not HealthyControl(before):
            raise ValueError("starting control failed; native verification batch is invalid")
        process_ids.add(before["pid"])
        build = before["build"]
        for sample in samples:
            entry = {"source_sha256": sample["sha256"], "path": sample["path"], "status": "failed", "measurement_status": "failed", "full_semantics_verified": False}
            report["cases"].append(entry)
            WriteJson(output, report)
            payload = sample["load"]()
            if hashlib.sha256(payload).hexdigest() != sample["sha256"]:
                raise ValueError("native batch source differs from its decoded input pin")
            document = open_document(payload, source_format=source_format, configuration=sample.get("configuration"), strict=True, include_brep=True, include_tessellation=False)
            entry["neutral_sha256"] = hashlib.sha256(document.to_json(indent=None).encode()).hexdigest()
            with closing(MeasureFile(application, availability, payload, suffix, "candidate", sample.get("configuration"))) as measurement:
                work, result = next(measurement)
                entry["measurement"] = result
                if not CheckMeasurement(result):
                    entry["reason"] = result.get("error", "native load or rebuild measurement failed")
                    continue
                if result["pid"] in process_ids or result["build"] != build:
                    raise ValueError("native case did not use a fresh process and the same application build")
                process_ids.add(result["pid"])
                entry["checks"] = CompareDocument(document, result["rebuilt"], application)
                entry.update(AssessChecks(entry["checks"]))
                entry["edits"] = []
                for edit in result["edits"]:
                    saved = work / edit["saved"]
                    if saved.parent != work or saved.name != edit["saved"]:
                        raise ValueError("edited output escapes its private verification directory")
                    edited = ReadBytes(saved)
                    edited_document = open_document(edited, source_format=source_format, configuration=sample.get("configuration"), strict=True, include_brep=True, include_tessellation=False)
                    with closing(MeasureFile(application, availability, edited, suffix, "control", sample.get("configuration"))) as reopening:
                        _, reopened = next(reopening)
                        fresh = CheckMeasurement(reopened) and reopened["pid"] not in process_ids and reopened["build"] == build
                        process_ids.add(reopened.get("pid"))
                        checks = CompareDocument(edited_document, reopened["rebuilt"], application) if fresh else []
                    restored = SameValues(edit["restored"], result["rebuilt"])
                    changed = not SameValues(edit["measured"]["bodies"], result["rebuilt"]["bodies"])
                    measured = bool(fresh and restored and changed and SameValues(edit["measured"], reopened.get("rebuilt")))
                    assessment = AssessChecks(checks)
                    entry["edits"].append({"parameter": edit["parameter"], "saved_sha256": hashlib.sha256(edited).hexdigest(), "reopened": reopened, "checks": checks, "restored": restored, "geometry_changed": changed, **assessment, "measurement_status": "passed" if measured else "failed"})
                measured = bool(entry["edits"]) and all(item["measurement_status"] == "passed" for item in entry["edits"])
                entry["measurement_status"] = "passed" if measured else "failed"
                entry.update(AssessChecks(entry["checks"] + [check for edit in entry["edits"] for check in edit["checks"]]))
                if not measured:
                    entry.update(status="failed", full_semantics_verified=False)
            del payload
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as error:
        report["error"] = f"{type(error).__name__}: {error}"[:2048]
    finally:
        try:
            with closing(MeasureFile(application, availability, control, suffix, "control")) as measurement:
                _, after = next(measurement)
                report["controls"]["after"] = after
            healthy = HealthyControl(report["controls"].get("before", {})) and HealthyControl(after) and after["pid"] not in process_ids and after["build"] == build
        except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as error:
            healthy = False
            report["controls"]["after"] = {"status": "failed", "error": str(error)[:2048]}
        try:
            current = {str(path): FileHash(path) for base in (root / "src", root / "re/automation/NativeAcceptance") for path in base.rglob("*.py")}
            stable = sources == current
        except (OSError, ValueError):
            stable = False
        measured = not report.get("error") and report["cases"] and all(item["measurement_status"] == "passed" for item in report["cases"])
        report["measurement_status"] = "invalid_batch" if not healthy or not stable else "passed" if measured else "failed"
        report["semantic_gaps"] = sorted({sample["path"] + ":" + gap for sample in report["cases"] for gap in sample.get("semantic_gaps", [])})
        complete = bool(measured and all(item["full_semantics_verified"] for item in report["cases"]))
        report["full_semantics_verified"] = bool(complete and healthy and stable)
        report["live_batch_verified"] = report["full_semantics_verified"]
        report["status"] = report["measurement_status"] if report["measurement_status"] != "passed" else "passed" if complete else "failed" if any(item["status"] == "failed" for item in report["cases"]) else "unverified"
        if report["status"] != "passed":
            report["action"] = "Inspect failed checks and semantic_gaps in this report; incomplete or differing observations do not verify decoding"
        report["controls_healthy"] = healthy
        report["sources_unchanged"] = stable
        WriteJson(output, report)
    return report
