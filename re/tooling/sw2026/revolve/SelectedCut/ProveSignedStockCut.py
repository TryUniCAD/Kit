from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
from subprocess import check_output
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(HERE.parent), str(HERE.parent.parent / "EndModes"), str(ROOT / "src")]

from ProveSelectedRevCut import checked, dispatch, need


PACKET = "fa54b00919aec9116c36b0d16a2a447d59621a2e20118f67bb0a9c1eaea380e0"
RESULT = "66300aa22b70a44f0b70e3e45420b426827ed8ea149a8316199bb7ee9f200258"
REVERSE_PACKET = "36380d1259581b8594f977ca3970239cd7c2bfdb3d06811dc97afddee4bbe59d"
REVERSE_RESULT = "b310fcd0e0b25305aa2e97b2c9451673b174eac5c0376eb7cd55f4916a0ac292"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
SOURCE = "src/convert/adapters/solidworks/Core/TypedResolved/Revolves/SelectedCut/ReadRevCutOps.py"


def reverse_projection(raw, frame):
    from convert import open_document
    from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
    from interchange.Features.FeatureAngleRev import AngularRevolve

    document = open_document(raw, source_format="solidworks.sldprt", strict=True)
    cut, = (step for step in document.feature_timeline
            if step.operation.value == "cut" and isinstance(step.definition, AngularRevolve))
    vector = cut.definition.AxisDirection
    axis = (vector.x, vector.y, vector.z)
    expected = tuple(-value for value in PrincipalFrame(frame).AxisV)
    need(axis == expected, "the public revolve read lost the measured reversed sweep axis")
    return list(axis)


def verify(packet, reverse):
    packet_pin, result_pin = (REVERSE_PACKET, REVERSE_RESULT) if reverse else (PACKET, RESULT)
    job = json.loads(checked(packet / "Packet.json", packet_pin))
    results = packet / "Inspection"
    receipt = json.loads(checked(results / "Result.json", result_pin))
    need(receipt["packet_sha256"] == packet_pin and receipt["controls_healthy"]
         and receipt["distinct_processes"] == 6 and receipt["oracle_sha256"] == ORACLE
         and receipt["idle_after"] and receipt["passed"]
         and receipt["codec_revision"] == job["codec_revision"],
         "paired native sign tests lack correct controls or a construction pin")
    for role in ("before", "after"):
        phase = json.loads(checked(results / f"Control{role.title()}.json", receipt[role]["sha256"]))
        need(phase["oracle_identity"]["sha256"] == ORACLE and receipt[role]["passed"], "native control failed")
    cases = {}
    probes = (("Top", 22, 101), ("Right", 19, 102)) if reverse else (("Top", 19, 102), ("Right", 22, 101))
    for label, selected, untouched in probes:
        name = f"KitScope{label}" + ("Reverse" if reverse else "Disclosure")
        row = receipt["cases"][name]
        loc = results / name
        need(row["passed"] and row["tree_rows"] == 29 and len(row["phases"]) == 2
             and row["candidate_sha256"] == job["files"][f"Candidates/{name}.SLDPRT"],
             "signed cut needs both phases and an unchanged candidate")
        final = json.loads(checked(loc / "FreshReopen.json", row["phases"][1]["sha256"]))
        need(final["passed"] and final["oracle_identity"]["sha256"] == ORACLE
             and final["reopened"]["definition"]["reverse"] is reverse
             and final["open_status"] == {"opened": True, "errors": 0, "warnings": 0},
             "saved derivative did not open cleanly")
        saved = loc / "Saved.SLDPRT"
        item = dispatch(saved, row["saved_sha256"], observed=final)
        need(item["owners"]["selected_producer_id"] == selected
             and [value["atom_id"] for value in item["bodies"]] == [untouched, 103]
             and item["unexpected_runtime_reads"] == 0, "physical cut lineage changed")
        if reverse:
            item["reversed_public_axis"] = reverse_projection(
                checked(saved, row["saved_sha256"]), {"Top": "y", "Right": "x"}[label],
            )
        cases[label] = item
    return {
        "schema": "kit.sw2026.signed-selected-revolve-saved-read.v1",
        "native_result_sha256": result_pin,
        "packet_sha256": packet_pin,
        "source_revision": check_output(("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip(),
        "changed_source_sha256": {SOURCE: sha256((ROOT / SOURCE).read_bytes()).hexdigest()},
        "cases": cases,
        "guarded_processes": len(cases),
        "new_native_processes": 0,
        "new_heldout_credit": 0,
        "public_writer": False,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reverse", action="store_true")
    args = parser.parse_args()
    payload = (json.dumps(verify(args.packet, args.reverse), indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with args.output.open("xb") as stream:
        stream.write(payload)
    print(sha256(payload).hexdigest())
