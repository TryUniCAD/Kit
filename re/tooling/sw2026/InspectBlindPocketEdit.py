from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from shutil import copyfile

import Swapp
from AuthorBlindCutSources import BlindCutAuthor
from AuthorCurves import Recorder, digest, require, write_json
from InspectFresh import healthy, inspect
from OracleIdentity import application_identity


def phase(job, path, sha256, folder, *, edit_to=None):
    folder.mkdir()
    case = job["geometry"]
    roles = tuple(job["feature_roles"])
    recorder = Recorder(folder / "Record.json", {"phase": folder.name, "case": case})
    controller = model = None
    result = {"passed": False, "input_sha256": sha256}
    with Swapp.Dismisser() as monitor:
        try:
            require(digest(path) == sha256, "the trial input changed before open")
            recorder.call("fresh oracle idle guard", Swapp.sweep)
            controller = recorder.call("launch owned SOLIDWORKS", Swapp.Sw)
            identity = recorder.call("authenticate the native executable", application_identity, controller.app)
            require(identity["version_matches"] and identity["sha256"] == job["oracle_sha256"], "unexpected SOLIDWORKS executable")
            result["oracle_identity"] = identity
            author = BlindCutAuthor(controller.app, recorder, Swapp)
            model, errors, warnings = recorder.call("open pinned pocket part", controller.open, path)
            result["open"] = [model is not None, errors, warnings]
            require(result["open"] == [True, 0, 0], "the pocket part failed to open cleanly")
            author.model = model
            depth = case["cut_depth_mm"] if edit_to is not None else case["edit_depth_mm"]
            result["opened"] = author.snapshot(case, "opened", depth, roles=roles)
            if edit_to is not None:
                author.edit_depth(case, roles=roles)
                result["edited"] = recorder.data["edited"]
                result["dimension_edit"] = recorder.data["edit"]
                save = recorder.call("save owned edited pocket", controller.save_as, model, edit_to)
                require(save == (True, 0, 0) and edit_to.is_file(), "saving the edited pocket failed or warned")
                result["save"] = [*save]
                result["saved_sha256"] = digest(edit_to)
            else:
                parameter = author.get(model, "Parameter", f"D1@{roles[3]}")
                require(parameter is not None and not author.get(parameter, "ReadOnly")
                        and int(author.get(parameter, "DrivenState")) == 2, "fresh reopen lost its editable cut dimension")
                recorder.close_number("freshly reopened cut depth", author.get(parameter, "SystemValue"), depth / 1000)
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["exception"] = repr(error)
        finally:
            if controller is not None:
                try:
                    if model is not None:
                        recorder.call("close owned pocket part", controller.close_doc, model)
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                try:
                    controller.close()
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    result["input_immutable"] = path.is_file() and digest(path) == sha256
    result["dialogs"] = monitor.log
    result["passed"] = bool(result["passed"] and result["input_immutable"] and not result["dialogs"]
                            and not result.get("controller_diagnostics") and not recorder.data["cleanup_errors"])
    recorder.data.update(result=result, finished_at=time.time())
    recorder.flush()
    return result


def main():
    job_path = Path(sys.argv[1]).resolve(strict=True)
    job = json.loads(job_path.read_bytes())
    candidate, control = (Path(job[key]).resolve(strict=True) for key in ("candidate", "control"))
    output = Path(job["output"]).resolve()
    require(job["schema"] == "kit.sw2026.blind-pocket-edit-job.v1", "unexpected generated pocket job")
    require(candidate.suffix.lower() == control.suffix.lower() == ".sldprt"
            and digest(candidate) == job["candidate_sha256"] and digest(control) == job["control_sha256"],
            "generated pocket or control does not match the frozen input")
    require(len(set(job["feature_roles"])) == len(job["feature_roles"]) == 4
            and all(re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*", name) for name in job["feature_roles"]),
            "expected exactly four authored feature names")
    checkout = Path(job["checkout_root"]).resolve()
    require(not any(path.is_relative_to(checkout) for path in (candidate, control, output)),
            "native pocket measurement paths must be external to the checkout")
    output.mkdir(exist_ok=False)
    working, edited = (output / name for name in ("WorkingPocket.SLDPRT", "EditedPocket.SLDPRT"))
    copyfile(candidate, working)
    result = {
        "schema": "kit.sw2026.blind-pocket-edit.v1", "started_at": time.time(),
        "job_sha256": digest(job_path), "oracle_sha256": job["oracle_sha256"],
        "candidate_sha256": job["candidate_sha256"], "controls": [], "phases": [],
        "heldout_acceptance": False, "accepted_production_parts": 0, "passed": False,
    }

    def checkpoint():
        write_json(output / "Inspection.json", result)

    def control_phase(label):
        row = {"kind": label}
        result["controls"].append(row)
        inspect(control, result=row, checkpoint=checkpoint)
        row["healthy"] = bool(healthy(row) and row["sha256"] == job["control_sha256"]
                              and row["oracle_identity"]["sha256"] == job["oracle_sha256"])
        return row["healthy"]

    try:
        if control_phase("before"):
            first = phase(job, working, job["candidate_sha256"], output / "Edit", edit_to=edited)
            result["phases"].append(first)
            checkpoint()
            if first["passed"]:
                result["phases"].append(phase(job, edited, first["saved_sha256"], output / "Reopen"))
    except Exception as error:
        result["exception"] = repr(error)
    finally:
        control_phase("after")
        rows = result["phases"]
        births = [row.get("oracle_identity", {}).get("process_creation_filetime")
                  for row in (*rows, *result["controls"])]
        result["distinct_processes"] = len({identity for identity in births if type(identity) is int and identity > 0})
        result["controls_healthy"] = [row.get("healthy") for row in result["controls"]] == [True, True]
        result["frozen_inputs_immutable"] = digest(candidate) == job["candidate_sha256"] and digest(control) == job["control_sha256"]
        if len(rows) == 2 and all(row["passed"] for row in rows):
            result["tree_unchanged"] = rows[0]["opened"]["tree"] == rows[0]["edited"]["tree"] == rows[1]["opened"]["tree"]
        result["passed"] = bool(result["distinct_processes"] == 4 and result["controls_healthy"]
                                and result["frozen_inputs_immutable"] and result.get("tree_unchanged") and not result.get("exception"))
        result["finished_at"] = time.time()
        checkpoint()
    print(json.dumps({key: result[key] for key in ("passed", "distinct_processes", "controls_healthy")}))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
