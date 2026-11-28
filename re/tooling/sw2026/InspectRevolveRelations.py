from __future__ import annotations

import json
from pathlib import Path
import sys

import Swapp
from AuthorCurves import digest, require, write_json
from AuthorRevolveEnds import RevolveEndAuthor, read_constants
from AuthorRevolveSources import run_phase
from InspectFresh import healthy, inspect


def constraint_codes():
    library = Swapp.pythoncom.LoadRegTypeLib(
        "{4687F359-55D0-4CD3-B6CF-2EB42C11F989}", 34, 0, 0
    )
    require(library.GetLibAttr()[3:5] == (34, 0), "wrong registered SwConst version")
    info, = (library.GetTypeInfo(index) for index in range(library.GetTypeInfoCount())
             if library.GetDocumentation(index)[0] == "swConstraintType_e")
    members = [info.GetVarDesc(index) for index in range(info.GetTypeAttr().cVars)]
    return {member.value: info.GetNames(member.memid)[0] for member in members}


class RelationObserver(RevolveEndAuthor):
    codes = {}

    def snapshot(self, case, label, angle_degrees):
        feature = super().snapshot(case, label, angle_degrees)
        manager = self.get(self.sketch, "RelationManager")
        rows = self.get(manager, "GetRelations", 0) or ()
        count = int(self.get(manager, "GetRelationsCount", 0))
        require(count == len(rows), "relation count and enumeration disagree")
        output = []
        for raw in rows:
            relation = self.typed(raw, "SketchRelation")
            code = int(self.get(relation, "GetRelationType"))
            observed = {"code": code, "name": self.codes.get(code), "owners": []}
            for item in self.get(relation, "GetEntities") or ():
                owner = self.typed(item, "SketchSegment")
                kind = int(self.get(owner, "GetType"))
                observed["owners"].append({
                    "id": list(self.get(owner, "GetID")),
                    "name": str(self.get(owner, "GetName")),
                    "kind": kind,
                    "construction": bool(self.get(owner, "ConstructionGeometry")),
                })
            output.append(observed)
        self.rec.data[label]["relations"] = output
        self.rec.flush()
        return feature


def main():
    job_path = Path(sys.argv[1])
    job = json.loads(job_path.read_bytes())
    spec = Path(job["spec"])
    control = Path(job["control"])
    require(digest(spec) == job["spec_sha256"] and digest(control) == job["control_sha256"], "relation probe input changed")
    case, = (value for value in json.loads(spec.read_bytes())["cases"] if value["name"] == job["case"])
    original = Path(job["source"])
    require(digest(original) == job["source_sha256"], "relation source changed")
    output = Path(job["output"])
    require(not output.exists(), "relation probe needs a fresh directory")
    output.mkdir()
    RelationObserver.constants = read_constants()
    RelationObserver.codes = constraint_codes()
    controls = []
    phase, pin = {}, None
    for label in ("before", "after"):
        measured = inspect(control)
        target = output / (label + ".json")
        write_json(target, measured)
        controls.append(healthy(measured) and measured["oracle_identity"]["sha256"] == job["oracle_sha256"])
        if label == "before" and controls[0]:
            phase, pin = run_phase(case, "edited-reopen", original, job["oracle_sha256"], job["source_sha256"],
                                   record_path=output / "Relations.json", author_type=RelationObserver)
    result = {"passed": all(controls) and bool(phase.get("passed")), "controls": controls,
              "source_sha256": job["source_sha256"], "phase_sha256": pin,
              "relations": phase.get("reopened", {}).get("relations", ()),
              "failure": phase.get("first_failure")}
    write_json(output / "Summary.json", result)
    Swapp.emit(result)
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
