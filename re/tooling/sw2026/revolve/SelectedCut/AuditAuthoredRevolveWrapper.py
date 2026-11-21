from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent.parent / "EndModes"))

from ProveSelectedRevCut import BUILD, checked, dispatch, need
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


LOCK = "e1bfa582944a409d8525cf9485bf40ed9ef99fa787c5c9678e4aa0011126b80f"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CASES = {"KitScopeTopDisclosure", "KitScopeRightDisclosure", "KitScopeTopReverse", "KitScopeRightReverse"}
FAULTS = ("wrong-result", "detached-face", "wrong-clock", "wrong-mirror")


def wrapper(raw):
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    cut, = (node for node in link.ResolvedValue.RootsValue if node.ClassValue.NameValue == "moRevCut_c")
    fields = cut.FieldsValue["f548"]["items"][0]["o"].FieldsValue
    return {"cache_words": [fields[key] for key in ("f108", "f104", "f100")],
            "consumed_atoms": [row["v"] for row in fields["f110"]], "face_class": fields["ff0"].ClassValue.NameValue}


def audit(folder):
    need(folder.parts[-2:] == ("ScopedRevolveAuthored04", "Capture"), "use only the signed disclosed capture")
    lock = json.loads(checked(folder / "SourceLock.json", LOCK))
    need(lock["oracle_build"] == BUILD and lock["oracle_sha256"] == ORACLE and lock["passed"]
         and lock["idle_after"] and lock["inputs_unchanged"] and lock["tools_unchanged"] and lock["writer_output_count"] == 0
         and lock["distinct_processes"] == lock["fresh_processes"] == 14
         and {item["case"] for item in lock["sources"]} == CASES, "disclosed source lock failed")
    ids, outcomes = [], {}
    for role in ("control-before", "control-after"):
        row = lock[role]
        phase = json.loads(checked(folder / f"{role}.json", row["sha256"]))
        need(row["passed"] and phase["oracle_identity"]["sha256"] == ORACLE and phase["opened"]
             and phase["rebuilt"] and phase["open_errors"] == phase["open_warnings"] == 0 and not phase["dialogs"],
             "native control failed or used a different build")
        ids.append(phase["oracle_identity"]["process_creation_filetime"])
    for source in lock["sources"]:
        name = source["case"]
        phases = {}
        for row in source["phases"]:
            role = row["phase"]
            stem = name + ("-edited" if role == "edited-reopen" else "")
            phase = json.loads(checked(folder / name / f"{stem}.{role}.json", row["sha256"]))
            need(source["passed"] and row["passed"] and phase["passed"] and phase["inspection_completed"]
                 and phase["source_immutable"] and phase["oracle_identity"]["sha256"] == ORACLE
                 and row["checks"] == row["checks_passed"] and not phase["dialogs"], "disclosed native phase failed")
            ids.append(phase["oracle_identity"]["process_creation_filetime"])
            phases[role] = phase
        need(set(phases) == {"author", "reopen", "edited-reopen"}, "disclosed case lacks one phase")
        initial = phases["reopen"]
        edit = initial["edited_derivative"]
        need(edit["save_status"] == [True, 0, 0] and initial["edit"]["passed"], "D1 edit was not saveable")
        states = (("original", name, source["native_sha256"], initial),
                  ("edited", name + "-edited", edit["sha256"], phases["edited-reopen"]))
        outcomes[name] = {}
        for state, stem, pin, phase in states:
            file = folder / name / f"{stem}.SLDPRT"
            words = wrapper(checked(file, pin))
            proof = dispatch(file, pin, observed=phase)
            result = proof["owners"]["result_atom_id"]
            expected = [-1, 0, 0] if name == "KitScopeTopReverse" else [-1, result, 58]
            need(words == {"cache_words": expected, "consumed_atoms": [proof["owners"]["consumed_atom_id"]],
                           "face_class": "moFaceRef_c"}, "face or cache-word route disagrees with the actual owners")
            need(proof["unexpected_runtime_reads"] == 0 and len(proof["exact_streams"]) == 2, "reader did not preserve its linked archives")
            outcomes[name][state] = {"sha256": pin, "wrapper": words, "strict_projection": proof}
    need(len(set(ids)) == len(ids) == 14 and all(ids[0] < item < ids[1] for item in ids[2:]),
         "disclosed phases outside the native control bracket")
    name = "KitScopeTopReverse"
    source = folder / name / f"{name}.SLDPRT"
    refused = {fault: dispatch(source, outcomes[name]["original"]["sha256"], fault=fault) for fault in FAULTS}
    return {"schema": "kit.sw2026.disclosed-revolve-face-cache.v1", "source_lock_sha256": LOCK, "oracle_build": BUILD,
            "oracle_sha256": ORACLE, "native_controlled_processes": 14, "strict_reads": 8, "exact_linked_streams": 16,
            "cases": outcomes, "cacheless_faults_refused": refused, "public_writer": False, "heldout_credit": 0, "passed": True}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = (json.dumps(audit(args.capture), indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with args.output.open("xb") as output:
        output.write(raw)
    print(sha256(raw).hexdigest())
