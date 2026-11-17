from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import time

from AuthorAssemblySources import run_phase
from AuthorCurves import digest, require, write_json
from InspectFresh import healthy, inspect


SCHEMA = "kit.sw2026.combined-planar-mate-discovery-author.v1"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
SCRIPT = Path(__file__).resolve()
TOOLS = ("AssemblyMateEvidence.py", "AuthorAssemblySources.py", "AuthorCurves.py", "InspectCircleSketch.py",
         "InspectFresh.py", "ObserveAssemblyLoad.py", "OracleIdentity.py", "Swapp.py", SCRIPT.name)


def verify(path, sha):
    root = path.parent
    require(digest(path) == sha, "disclosed combined-mate packet has changed")
    job = json.loads(path.read_bytes())
    require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE and job["synchronize_owned_children"] is True,
            "the author's scope must be the pinned ordinary assembly fixture")
    tools = root / "Tools"
    require(SCRIPT.parent == tools and set(job["tools_sha256"]) == set(TOOLS), "the staged author tool set differs")
    require(all(digest(tools / name) == job["tools_sha256"][name] for name in TOOLS), "an assembly author tool changed")
    control = root / "Control.SLDPRT"
    require(digest(control) == job["control_sha256"], "native disclosed rectangle control changed")
    case = job["case"]
    require(case["split"] == "discovery" and re.fullmatch(r"A[0-9]{2}Combined[A-Za-z]+", case["name"])
            and set(row["kind"] for row in case["mates"]) <= {"coincident", "parallel", "distance"}
            and len(case["mates"]) >= 2 and len(case["placements"]) >= 2
            and any(row["kind"] == "distance" for row in case["mates"]), "a disclosed combined-mate design is required")
    require(re.fullmatch(r"[0-9a-f]{40}", job["source_revision"]), "the authoring source revision must be pinned")
    return job, case, control


def run(path, sha):
    require(os.name == "nt", "native assembly authoring requires the Windows guest")
    job, case, control = verify(path, sha)
    root = path.parent
    output = root / "Native"
    output.mkdir()
    report = output / "SourceEvidence.json"
    evidence = {"schema": SCHEMA, "packet_sha256": sha, "started_at": time.time(), "phases": [],
                "controls": [], "writer_output_count": 0, "heldout_inputs_read": 0, "passed": False}

    def checkpoint():
        write_json(report, evidence)

    def bracket(role):
        row = {"role": role}
        evidence["controls"].append(row)
        inspect(control, result=row, checkpoint=checkpoint)
        row["passed"] = healthy(row) and row["oracle_identity"]["sha256"] == ORACLE
        checkpoint()
        return row

    checkpoint()
    try:
        before = bracket("ControlBefore")
        if before["passed"]:
            authored = run_phase(case, "author", output, job, control, before["mass"])
            evidence["phases"].append(authored)
            checkpoint()
            if authored["passed"]:
                reopened = run_phase(case, "fresh-reopen", output, job, control, before["mass"], prior=authored)
                evidence["phases"].append(reopened)
                checkpoint()
    finally:
        bracket("ControlAfter")
        rows = [*evidence["controls"], *evidence["phases"]]
        stamps = {row.get("oracle_identity", {}).get("process_creation_filetime") for row in rows}
        evidence["passed"] = (len(rows) == 4 and len(stamps) == 4 and all(type(value) is int and value > 0 for value in stamps)
                              and all(row.get("passed", False) for row in rows)
                              and digest(control) == job["control_sha256"])
        evidence["finished_at"] = time.time()
        checkpoint()
    return evidence


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    path = args.packet.resolve(strict=True)
    if args.command == "verify":
        verify(path, args.packet_sha256)
        result = {"passed": True, "native_processes_started": 0, "heldout_inputs_read": 0}
    else:
        recorded = run(path, args.packet_sha256)
        result = {"passed": recorded["passed"], "native_processes": len(recorded["controls"]) + len(recorded["phases"]),
                  "heldout_inputs_read": 0}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
