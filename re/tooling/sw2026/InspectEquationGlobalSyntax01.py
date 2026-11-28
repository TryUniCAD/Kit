from __future__ import annotations

import argparse
import json
from pathlib import Path

import AuthorEquationSources01 as baseline
from AuthorRectangleAnchors import RectangleAuthor

CASES = (
    {
        "id": "Baseline",
        "index": 0,
        "text": '"source_width" = 31.7 mm',
        "solve": False,
        "binding": "registered_invoketypes",
        "factor": "exact previous call",
    },
    {
        "id": "AdjacentUnit",
        "index": 0,
        "text": '"source_width" = 31.7mm',
        "solve": False,
        "binding": "registered_invoketypes",
        "factor": "unit adjacency only",
    },
    {
        "id": "ImmediateSolve",
        "index": 0,
        "text": '"source_width" = 31.7 mm',
        "solve": True,
        "binding": "registered_invoketypes",
        "factor": "Solve only",
    },
    {
        "id": "Append",
        "index": -1,
        "text": '"source_width" = 31.7 mm',
        "solve": False,
        "binding": "registered_invoketypes",
        "factor": "append index only",
    },
    {
        "id": "NoUnit",
        "index": 0,
        "text": '"source_width" = 31.7',
        "solve": False,
        "binding": "registered_invoketypes",
        "factor": "unit suffix removed only",
    },
    {
        "id": "SimpleName",
        "index": 0,
        "text": '"B" = 31.7 mm',
        "solve": False,
        "binding": "registered_invoketypes",
        "factor": "global name only",
    },
    {
        "id": "GeneratedMethod",
        "index": 0,
        "text": '"source_width" = 31.7 mm',
        "solve": False,
        "binding": "generated_method",
        "factor": "actual generated interface method only",
    },
    {
        "id": "PublishedLiteral",
        "index": 0,
        "text": '"B" = 2',
        "solve": False,
        "binding": "registered_invoketypes",
        "factor": "independent official global-assignment control; multiple input differences",
    },
)


def observe_manager(author, manager, stage):
    result = {
        "stage": stage,
        "count": int(author.eq(manager, "GetCount", 1)),
        "rows": [],
    }
    baseline.require(
        0 <= result["count"] <= 2,
        "the single-global matrix document has an unexpected equation count",
    )
    for index in range(result["count"]):
        text = str(author.eq(manager, "Equation", 2, index))
        row = {
            "index": index,
            "text": text,
            "status_after_text": int(author.eq(manager, "Status")),
            "global_variable": bool(author.eq(manager, "GlobalVariable", 2, index)),
            "disabled": bool(author.eq(manager, "Disabled", 2, index)),
        }
        row["raw_value"] = float(author.eq(manager, "Value", 2, index))
        row["status_after_value"] = int(author.eq(manager, "Status"))
        row["raw_value_unit_domain"] = (
            "unqualified native value; source geometry and dimensions are measured independently in SI"
        )
        result["rows"].append(row)
    return result


def run_case(author, controller, case, row):
    baseline.require(
        author.model is None,
        "each matrix member requires a genuinely new native document",
    )
    native_case = {
        "kind": "corner",
        "width_m": case["width_mm"] / 1000,
        "height_m": case["height_mm"] / 1000,
        "depth_m": case["depth_mm"] / 1000,
    }
    author.build(controller, native_case)
    result = {
        "intent": row,
        "document_title": str(author.get(author.model, "GetTitle")),
        "document_path": str(author.get(author.model, "GetPathName")),
        "body_before": RectangleAuthor.snapshot(author, native_case, "Original"),
        "add2_return": None,
        "call_error": None,
        "publication_observed": False,
    }
    baseline.require(
        result["document_path"] == "",
        "a matrix document unexpectedly has a persisted input path",
    )
    manager = author.manager()
    result["before"] = observe_manager(author, manager, "before_add")
    baseline.require(
        result["before"]["count"] == 0,
        "new native matrix document already owns equations",
    )
    author.rec.data["current_member"] = result
    author.rec.flush()
    try:
        if row["binding"] == "registered_invoketypes":
            result["add2_return"] = author.eq(
                manager, "Add2", 1, row["index"], row["text"], row["solve"]
            )
        else:
            result["add2_return"] = author.rec.call(
                "IEquationMgr.Add2 generated interface method",
                manager.Add2,
                row["index"],
                row["text"],
                row["solve"],
                parameters={
                    "index": row["index"],
                    "equation": row["text"],
                    "solve": row["solve"],
                    "interface_iid": "{02272CE8-FE52-4B94-B120-6D1826FDBE32}",
                    "binding": "actual installed release-34.0 generated method; no copied interop code",
                },
            )
    except Exception as error:
        result["call_error"] = {"type": type(error).__name__, "error": repr(error)}
    result["status_immediately_after_add2"] = int(author.eq(manager, "Status"))
    author.rec.flush()
    result["immediate"] = observe_manager(author, manager, "immediately_after_add")
    author.rec.flush()
    result["evaluate_all_return_ungraded"] = author.eq(manager, "EvaluateAll", 1)
    result["status_after_evaluation"] = int(author.eq(manager, "Status"))
    result["evaluated"] = observe_manager(author, manager, "after_evaluate_all")
    author.rec.flush()
    observed = result["evaluated"]["rows"]
    result["publication_observed"] = (
        result["evaluated"]["count"] == 1
        and len(observed) == 1
        and "".join(observed[0]["text"].split()) == "".join(row["text"].split())
        and observed[0]["global_variable"]
        and not observed[0]["disabled"]
    )
    result["body_after"] = RectangleAuthor.snapshot(author, native_case, "Original")
    result["tree_unchanged"] = (
        result["body_after"]["tree"] == result["body_before"]["tree"]
    )
    baseline.require(
        result["body_after"]["relations"] == result["body_before"]["relations"],
        "unbound global assignment changed the base source sketch relation owners",
    )
    result["diagnostic_completed"] = True
    return result


def matrix(path, sha):
    job = baseline.read_job(path, sha)
    baseline.guest_only(job)
    baseline.require(
        job["global_syntax_matrix"]["cases"] == list(CASES)
        and job["global_syntax_matrix"]["writer_output_count"] == 0,
        "the independently frozen global-syntax matrix differs",
    )
    directory, case, seal = baseline.load_case(path, job, "D01")
    out = directory / "Inspection" / "Matrix"
    out.mkdir(parents=True, exist_ok=False)
    from OracleIdentity import application_identity
    import Swapp

    rec = baseline.Recorder(
        out / "Record.json",
        {
            "protocol_sha256": sha,
            "intent_sha256": seal["intent_sha256"],
            "phase": "Matrix",
            "diagnostic_only": True,
        },
    )
    result = {
        "diagnostic_completed": False,
        "native_acceptance": False,
        "writer_output_count": 0,
        "native_files_saved": 0,
        "sealed_inputs_read": 0,
        "cases": [],
    }
    controller, author, lease = None, None, None
    with Swapp.Dismisser() as dialogs:
        try:
            rec.call(
                "verify idle oracle for disclosed global syntax matrix", Swapp.sweep
            )
            controller = rec.call("start one owned matrix oracle", Swapp.Sw)
            identity = rec.call(
                "verify exact matrix oracle", application_identity, controller.app
            )
            baseline.require(
                identity["sha256"] == baseline.ORACLE
                and identity["version_matches"]
                and controller.revision == "34.5.2",
                "the native matrix build differs",
            )
            result["oracle_identity"] = identity
            rec.data["oracle_identity"] = identity
            author = baseline.EquationAuthor(
                controller.app,
                rec,
                Swapp,
                json.loads((path.parent / "ApiMetadata01.json").read_bytes()),
            )
            journal = directory / "Inspection" / "Author" / "PreferenceLease.json"
            journal.parent.mkdir(parents=True, exist_ok=False)
            lease = baseline.PromptLease(author, journal)
            lease.enter()
            for row in CASES:
                value = run_case(author, controller, case, row)
                result["cases"].append(value)
                rec.data["result"] = result
                rec.flush()
                rec.call(
                    "close only the fresh unsaved matrix document",
                    controller.close_doc,
                    author.model,
                )
                author.model = None
                baseline.require(
                    int(author.get(author.app, "GetDocumentCount")) == 0,
                    "a previous matrix document remains open",
                )
            result["diagnostic_completed"] = True
        except Exception as error:
            rec.failure(error)
        finally:
            if lease is not None:
                try:
                    lease.restore()
                except Exception as error:
                    rec.failure(error, cleanup=True)
                    result["diagnostic_completed"] = False
            if controller is not None:
                try:
                    rec.call(
                        "close only the owned matrix application", controller.close
                    )
                except Exception as error:
                    rec.failure(error, cleanup=True)
                    result["diagnostic_completed"] = False
                if controller.diagnostics:
                    result["controller_diagnostics"] = controller.diagnostics
                    result["diagnostic_completed"] = False
    result["dialog_log"] = dialogs.log
    if dialogs.log or rec.data["cleanup_errors"]:
        result["diagnostic_completed"] = False
    result["numeric_checks"] = len(rec.data["checks"])
    result["published_case_ids"] = [
        row["intent"]["id"] for row in result["cases"] if row["publication_observed"]
    ]
    rec.data["result"] = result
    rec.data["passed"] = result["diagnostic_completed"]
    rec.flush()
    baseline.write_json(out / "Result.json", result)
    return {
        key: result[key]
        for key in (
            "diagnostic_completed",
            "native_acceptance",
            "writer_output_count",
            "native_files_saved",
            "sealed_inputs_read",
            "numeric_checks",
            "published_case_ids",
        )
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument(
        "command",
        choices=(
            "verify",
            "seal",
            "ControlBefore",
            "Matrix",
            "ControlAfter",
            "summary",
        ),
    )
    args = parser.parse_args()
    job = baseline.read_job(args.job, args.sha256)
    baseline.require(
        job["global_syntax_matrix"]["cases"] == list(CASES),
        "the global matrix scope differs",
    )
    if args.command == "verify":
        result = {
            "passed": True,
            "files": len(job["files_sha256"]),
            "native_processes_started": 0,
            "sealed_inputs_read": 0,
        }
    elif args.command == "seal":
        result = baseline.seal_intents(args.job, args.sha256, "D01")
    elif args.command.startswith("Control"):
        result = baseline.phase(args.job, args.sha256, "D01", args.command)
    elif args.command == "Matrix":
        result = matrix(args.job, args.sha256)
    else:
        source = args.job.parent / "Disclosed/D01/Inspection"
        records = {}
        missing = []
        for name in ("ControlBefore", "Matrix", "ControlAfter"):
            file = source / name / "Result.json"
            if not file.is_file():
                missing.append(name)
            else:
                records[name] = json.loads(file.read_bytes())
        identities = [
            (
                row["oracle_identity"]["process_id"],
                row["oracle_identity"]["process_creation_filetime"],
            )
            for row in records.values()
            if row.get("oracle_identity")
        ]
        healthy = all(
            records.get(name, {}).get("passed") is True
            and records.get(name, {}).get("open_status") == [0, 0]
            for name in ("ControlBefore", "ControlAfter")
        )
        completed = (
            healthy
            and not missing
            and records.get("Matrix", {}).get("diagnostic_completed") is True
            and len(set(identities)) == 3
        )
        result = {
            "diagnostic_completed": completed,
            "controls_healthy": healthy,
            "distinct_processes": len(set(identities)),
            "writer_output_count": 0,
            "native_acceptance": False,
            "native_files_saved": 0,
            "published_case_ids": records.get("Matrix", {}).get(
                "published_case_ids", []
            ),
            "missing_phases": missing,
            "result_sha256": {
                name: baseline.digest(source / name / "Result.json") for name in records
            },
            "numeric_checks": sum(
                row.get("numeric_checks", 0) for row in records.values()
            ),
        }
        baseline.write_json(args.job.parent / "GlobalSyntaxResult.json", result)
    print(json.dumps(result, sort_keys=True))
    return (
        0
        if result.get(
            "passed",
            result.get(
                "diagnostic_completed", result.get("native_processes_started") == 0
            ),
        )
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
