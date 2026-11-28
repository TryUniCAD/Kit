from argparse import ArgumentParser
from hashlib import sha256
import json
from math import tau
from pathlib import Path
from subprocess import check_output
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
TRIAL_PIN = "03673e04df2f3d8c8a98f1a3ad6784deba549fad0e353c0797f6de8d8708c61d"
RESULT_PIN = "ae342e6f39afcacf48db0936c67c715bae7bc0199abdeb3dd8afd4aaf172b4e8"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
SCHEMA = "kit.sw2026.selected-revolve-cut-saved-owner-contrast.v1"
STOCKS = ("InnerRevolveStock", "OuterRevolveStock")


def digest(raw):
    return sha256(raw).hexdigest()


def measured(path, pin):
    assert path.is_file() and not path.is_symlink()
    raw = path.read_bytes()
    assert digest(raw) == pin
    return raw


def normalize_drivers(rows, owner):
    assert set(rows) == set(STOCKS)
    result = {}
    for stock in STOCKS:
        row = rows[stock]
        assert row["name"] == "D1@" + stock + "@" + owner + ".Part"
        assert row["radians"] == tau and type(row["parents"]) is list and len(row["parents"]) == 2
        result[stock] = {"driver_name": "D1", "feature_name": stock,
                         "radians": row["radians"], "parents": row["parents"]}
    return result


def saved_state(raw):
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    link = ReadNativeLink(SldprtArchive.from_bytes(raw), 0)
    cut, = (node for node in link.ResolvedValue.RootsValue if node.ClassValue.NameValue == "moRevCut_c")
    wrapper, = (entry["o"] for entry in cut.FieldsValue["f548"]["items"])
    fields = wrapper.FieldsValue
    cad = open_document(raw, source_format="solidworks.sldprt", strict=True)
    return {"decoded_body_count": len(cad.bodies), "decoded_solid_count": len(cad.brep.bodies) if cad.brep else 0,
            "diagnostic_codes": [item.code for item in cad.diagnostics],
            "body_wrapper": {key: fields[key] for key in ("f18", "f100", "f104", "f108")},
            "face_representative_absent": fields["ff0"] is None}


def audit(root, output):
    sys.path.insert(0, str(ROOT / "src"))
    manifest = json.loads(measured(root / "Trial.json", TRIAL_PIN))
    result = json.loads(measured(root / "Inspection/Result.json", RESULT_PIN))
    assert result["trial_sha256"] == TRIAL_PIN and result["oracle_sha256"] == ORACLE
    assert result["diagnostic_completed"] and result["control_brackets_healthy"] and result["idle_after"]
    assert result["before"]["passed"] and result["after"]["passed"] and result["distinct_processes"] == 6
    assert result["lifecycle_passed"] is False and result["heldout_credit"] == 0 and not result["public_writer"]
    for name, row in (("ControlBefore", result["before"]), ("ControlAfter", result["after"])):
        measured(root / "Inspection" / (name + ".json"), row["sha256"])
    observed = {}
    model = manifest["case"]["name"]
    for label in ("producer", "sentinel"):
        arm = result["arms"][label]
        assert arm["complete"] is False and arm["tree_rows"] == 29
        location = root / "Inspection" / label
        first, last = (json.loads(measured(location / file, summary["sha256"]))
                       for file, summary in zip(("Initial.json", "FreshReopen.json"), arm["phases"], strict=True))
        assert first["passed"] and last["passed"] and first["edit"]["passed"]
        assert first["edited_derivative"]["sha256"] == arm["edited_sha256"]
        for phase in (first, last):
            assert phase["open_status"] == {"opened": True, "errors": 0, "warnings": 0}
            assert phase["before_explicit_rebuild"]["bodies"] == 2 and phase["before_explicit_rebuild"]["whats_wrong"] == 0
            assert phase["oracle_identity"]["sha256"] == ORACLE and phase["first_failure"] is None
        states = (first["reopened"], first["edited"], last["reopened"])
        assert len(states[0]["features"]) == 29 and all(row["features"] == states[0]["features"]
                                                       and row["parents"] == states[0]["parents"] for row in states)
        owners = (model, model, model + "-edited")
        drivers = [normalize_drivers(row["stock_drivers"], title) for row, title in zip(states, owners, strict=True)]
        assert drivers[0] == drivers[1] == drivers[2] and states[0]["stock_drivers"] != states[2]["stock_drivers"]
        raw = measured(location / "Saved.SLDPRT", arm["edited_sha256"])
        data = saved_state(raw)
        assert data["body_wrapper"]["f100"] == data["body_wrapper"]["f104"] == 0 and data["face_representative_absent"]
        observed[label] = {"native_lifecycle_matches": True, "native_cold_body_counts": [2, 2],
                           "tree_rows": 29, "stock_drivers": drivers[0], "document_owners": list(owners),
                           "saved_native_sha256": arm["edited_sha256"], "current_sdk_saved_read": data}
    assert not any(key in sys.modules for key in ("Swapp", "pythoncom", "pywintypes"))
    ref = check_output(("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()
    receipt = {"schema": SCHEMA, "trial_sha256": TRIAL_PIN, "original_result_sha256": RESULT_PIN,
               "source_revision": ref, "original_lifecycle_passed": False, "paired_native_lifecycles_confirmed": True,
               "new_oracle_processes": 0, "new_heldout_credit": 0, "public_writer": False, "arms": observed}
    raw = (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with output.open("xb") as file:
        file.write(raw)
    print(digest(raw))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit(args.packet, args.output)
