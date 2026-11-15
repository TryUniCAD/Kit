from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import Swapp
from OracleIdentity import application_identity


def inspect(path):
    Swapp.sweep()
    result = {"path": str(path), "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest()}
    with Swapp.Dismisser() as dismisser:
        controller = Swapp.Sw()
        try:
            result.update(revision=controller.revision, process_ids=sorted(Swapp.process_ids()))
            result["oracle_identity"] = application_identity(controller.app)
            if not result["oracle_identity"]["version_matches"]:
                raise RuntimeError("oracle executable differs from SOLIDWORKS 2026 SP05.2 build 34.5.2.0604")
            if not controller.revision.startswith(Swapp.EXPECTED_BUILD):
                raise RuntimeError(f"unexpected oracle revision: {controller.revision}")
            result.update(Swapp.measure(controller, path))
        except Exception as error:
            result["exception"] = repr(error)
        finally:
            controller.close()
            result["controller_diagnostics"] = controller.diagnostics
    result["dialogs"] = dismisser.log
    result["progress_windows"] = dismisser.progress
    return result


def healthy(result):
    features = result.get("features", ())
    return bool(result.get("opened") and result.get("rebuilt") and result.get("bodies", 0) > 0 and result.get("mass", {}).get("volume", 0) > 0 and result.get("open_errors") == 0 and result.get("open_warnings") == 0 and result.get("whats_wrong") == 0 and not result.get("exception") and not result.get("controller_diagnostics") and not result.get("dialogs") and not any(value.get("error") or value.get("warning") for value in features))


def main():
    job = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output = Path(sys.argv[2])
    result = {
        "authority": "clean-vendor-inspection", "instrumented": False,
        "started_at": time.time(), "results": [],
        "generator": job.get("generator"),
        "job_sha256": hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest(),
        "inspector_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    for kind, path in (("control_before", job["control"]), *(("candidate", path) for path in job["files"]), ("control_after", job["control"])):
        row = inspect(path)
        row["kind"] = kind
        row["geometry_and_rebuild_healthy"] = healthy(row)
        result["results"].append(row)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        Swapp.emit({"kind": kind, "opened": row.get("opened"), "bodies": row.get("bodies"), "healthy": row["geometry_and_rebuild_healthy"]})
    result["finished_at"] = time.time()
    result["controls_healthy"] = all(value["geometry_and_rebuild_healthy"] for value in result["results"] if value["kind"] != "candidate")
    result["vendor_acceptance"] = "incomplete; geometry inspection alone does not prove editing or save/reopen"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return int(not result["controls_healthy"] or not all(value["geometry_and_rebuild_healthy"] for value in result["results"]))


if __name__ == "__main__":
    raise SystemExit(main())
