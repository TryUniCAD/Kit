from argparse import ArgumentParser
from pathlib import Path
from subprocess import run
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "EndModes"))

from AuditRevEndOwners import ArchiveNode, ReadNativeLink, SldprtArchive, audit_streams, digest, guard_runtime


LOCK = "f3caaecc7fce3f4f2feb50cd09e24b2b2b9ef78779e493d10ac71b950854186b"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
BUILD = "34.5.2.0604"
CASES = ("ScopePairA", "ScopePairB")


def checked(path, known):
    data = path.read_bytes()
    if digest(data) != known:
        raise ValueError("disclosed cut artifact changed: " + path.name)
    return data


def source(capture, case, edited):
    lock = json.loads(checked(capture / "SourceLock.json", LOCK))
    assert lock["passed"] and lock["split"] == "discovery" and lock["family"] == "cut"
    assert lock["distinct_processes"] == 8 and lock["oracle_sha256"] == ORACLE and lock["oracle_build"] == BUILD
    assert tuple(row["case"] for row in lock["sources"]) == CASES
    assert lock["control-before"]["passed"] and lock["control-after"]["passed"] and lock["idle_after"]
    selected, = (row for row in lock["sources"] if row["case"] == case)
    author, initial, fresh = selected["phases"]
    assert selected["passed"] and author["passed"] and initial["passed"] and fresh["passed"]
    assert [row["phase"] for row in selected["phases"]] == ["author", "reopen", "edited-reopen"]
    read = json.loads(checked(capture / case / (case + ".reopen.json"), initial["sha256"]))
    last = json.loads(checked(capture / case / (case + "-edited.edited-reopen.json"), fresh["sha256"]))
    for phase in (read, last):
        assert phase["passed"] and phase["source_immutable"] and phase["oracle_identity"]["sha256"] == ORACLE
        assert phase["open_status"] == {"opened": True, "errors": 0, "warnings": 0}
        assert phase["reopened"]["body_count"] == 2 and phase["reopened"]["definition"]["scope"]["count"] == 2
    name = case + ("-edited" if edited else "") + ".SLDPRT"
    known = read["edited_derivative"]["sha256"] if edited else selected["native_sha256"]
    return checked(capture / case / name, known), known


def inspect(raw):
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    (cut,) = (node for node in link.ResolvedValue.RootsValue if isinstance(node, ArchiveNode)
              and node.ClassValue.NameValue == "moRevCut_c")
    fields = cut.FieldsValue
    assert fields["f544"] == fields["has_f548"] == 1 and fields["f780"] == {"n": 0, "items": []}
    assert fields["f548"]["n"] == fields["f530"]["n"] == fields["f528"]["n"] == 2
    consumed = [row["o"].FieldsValue for row in fields["f530"]["items"]]
    bodies = [row["o"].FieldsValue for row in fields["f528"]["items"]]
    assert all(row["f144"] == 1 and row["f12c"] == row["f130"] for row in consumed)
    assert all(row["f144"] == 0 and row["f12c"] == row["f130"] == fields["f08"] for row in bodies)
    input_ids = {row["f140"]: row["f12c"] for row in consumed}
    output_ids = {row["f140"] for row in bodies}
    assert len(input_ids) == len(output_ids) == 2 and not set(input_ids).intersection(output_ids)
    selection = []
    for member in fields["f548"]["items"]:
        node = member["o"]
        assert node.ClassValue.NameValue == "moCompSolidBody_c"
        wrapper = node.FieldsValue
        atom = wrapper["f18"]
        assert atom == wrapper["f1c"] and atom in input_ids
        assert wrapper["n110"] == 1 and tuple(row["v"] for row in wrapper["f110"]) == (atom,)
        assert wrapper["f108"] in (-1, input_ids[atom])
        assert wrapper["f104"] in output_ids or wrapper["f104"] == 0
        assert wrapper["ff0"] is not None
        selection.append({key: wrapper[key] for key in ("f18", "f1c", "f100", "f104", "f108", "n110")})
    assert {row["f18"] for row in selection} == set(input_ids)
    return {"selected_wrappers_in_wire_order": selection, "consumed_atom_producers": input_ids,
            "cut_output_atoms": sorted(output_ids), "body_feature_list_empty": True,
            "streams": audit_streams(archive, link)}


def worker(capture, case, edited):
    raw, known = source(capture, case, edited)
    blocked = guard_runtime()
    observed = inspect(raw)
    assert not blocked
    return {"case": case, "edited": edited, "source_sha256": known, "runtime_external_access_attempts": 0, **observed}


def main(capture, output):
    cases = []
    for case in CASES:
        for edited in (False, True):
            command = [sys.executable, "-I", "-B", __file__, str(capture), "--worker", case]
            if edited:
                command.append("--edited")
            result = run(command, check=True, capture_output=True, timeout=120)
            assert not result.stderr
            cases.append(json.loads(result.stdout))
    result = {"schema": "kit.sw2026.explicit-two-selected-revolve-cut.v1", "source_lock_sha256": LOCK,
              "oracle_build": BUILD, "cases": cases, "streams": sum(len(case["streams"]) for case in cases),
              "runtime_external_access_attempts": 0, "heldout_cases": 0, "writer_outputs": 0}
    data = (json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with output.open("xb") as destination:
        destination.write(data)
    print(digest(data))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("capture", type=Path)
    parser.add_argument("--worker", choices=CASES)
    parser.add_argument("--edited", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.capture, args.worker, args.edited), sort_keys=True))
    else:
        if args.output is None:
            parser.error("--output is required for the guarded multi-case audit")
        main(args.capture, args.output)
