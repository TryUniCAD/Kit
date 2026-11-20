from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
from math import isclose


ROOT = Path(__file__).resolve().parents[5]
LOCK = ROOT / "re/solidworks/v2026/heldout/PrincipalRevolveSourceLock01.json"
PREPARATION = ROOT / "re/solidworks/measurements/2026/SdkPrincipalRevolvePreparation01.json"
RIGHT = ROOT / "re/solidworks/measurements/2026/PrincipalRevolveRightSource01.json"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
ORACLE_VERSION = "34.5.2.0604"


def read(path):
    raw = path.read_bytes()
    return json.loads(raw), sha256(raw).hexdigest()


def tree(snapshot):
    items = []
    for row in snapshot["features"]:
        assert row["error"] == 0 and row["warning"] is False and row["suppressed"] is False
        dimensions = tuple(tuple(item["name"].split("@")[:2]) for item in row.get("dims", ()))
        items.append((row["name"], row["type"], dimensions))
    return tuple(items)


def compare(actual, expected):
    assert actual["bodies"] == expected["bodies"] == 1
    assert actual["parents"] == expected["parents"]
    assert actual["reverse"] == expected["reverse"]
    assert actual["forward_handedness"] == expected["forward_handedness"]
    assert isclose(actual["angle_radians"], expected["angle_radians"], rel_tol=1e-13)
    observed_tree = tree(actual)
    assert observed_tree == tree(expected)
    for point, target in zip(actual["axis"]["points"], expected["axis"]["points"], strict=True):
        assert all(isclose(x, y, abs_tol=1e-12) for x, y in zip(point, target, strict=True))
    observed = actual["mass"]
    reference = expected["mass"]
    for key in ("volume", "area", "mass"):
        assert format(observed[key], ".6g") == format(reference[key], ".6g")
    for value, target in zip(observed["com"], reference["com"], strict=True):
        zero = abs(value) <= 1e-12 and abs(target) <= 1e-12
        assert zero or format(value, ".6g") == format(target, ".6g")
    return {"features": len(observed_tree), "actual": observed, "reference": reference}


def compliant(row):
    assert row["passed"] and row["source_immutable"] and not row["dialogs"] and not row["cleanup_errors"]
    assert row["open_status"] == {"opened": True, "errors": 0, "warnings": 0}
    identity = row["oracle_identity"]
    assert identity["file_version"] == ORACLE_VERSION and identity["sha256"] == ORACLE


def main(generated, disclosed, right, output):
    lock, lock_sha = read(LOCK)
    right_manifest, right_manifest_sha = read(RIGHT)
    prep, prep_sha = read(PREPARATION)
    assert lock_sha == "9396b94d1d503a0389c1db4ce7711125429265b271694bbe28a890b49059dc48"
    assert right_manifest_sha == "83f0043cf3ce9a8c68ffbbc329681bfc3a887edc0f65851f9f8da7db44b09f01"
    assert prep["sealed_sources_read"] == 0
    report, report_sha = read(generated / "Inspection.json")
    assert report["passed"] and report["controls_healthy"] and report["distinct_processes"] == 10
    assert report["source_revision"] == prep["source_revision"] and report["oracle_sha256"] == ORACLE
    assert report["saved_edit_reopened"] and not report["heldout_acceptance"]
    sources = {row["name"]: (disclosed, row["phase_record_sha256"][1])
               for row in lock["cases"] if row["split"] == "discovery"}
    right_name = right_manifest["case"]["name"]
    right_phase = next(row for row in right_manifest["phases"] if row["role"] == "reopen")
    sources[right_name] = (right, right_phase["record_sha256"])
    candidates = {row["request"]["spec"]["name"]: row["proof"]["sha256"]
                  for row in prep["cases"] if not row["request"].get("alteration")}
    assert len(candidates) == len(sources) == 4
    contrasts = []
    for artifact, derivative in zip(report["cases"], report["derivative_reopens"], strict=True):
        name = artifact["job"]["case"]["name"]
        case = name.removeprefix("Kit")
        directory, source_pin = sources[case]
        native, native_sha = read(directory / f"{case}.reopen.json")
        assert native_sha == source_pin
        assert name == derivative["job"]["case"]["name"] and artifact["source_sha256"] == candidates[name]
        assert artifact["generator_receipt_sha256"] == prep_sha
        for observation in (native, artifact, derivative):
            compliant(observation)
        for opened in (artifact, derivative):
            before = opened["before_explicit_rebuild"]
            assert (before["bodies"], before["needs_rebuild"], before["whats_wrong"]) == (1, 0, 0)
        assert native["edit"]["passed"] and artifact["edit"]["passed"] and artifact["edit"]["setter_status"] == 0
        assert artifact["edited_derivative"]["save_status"] == [True, 0, 0]
        assert derivative["source_sha256"] == artifact["edited_derivative"]["sha256"]
        contrasts.append({
            "native_case": case, "source_reopen_sha256": native_sha, "generated_sha256": candidates[name],
            "initial": compare(artifact["reopened"], native["reopened"]),
            "edited": compare(artifact["edited"], native["edited"]),
            "saved_edit": compare(derivative["reopened"], native["edited"]),
        })
    assert {row["native_case"] for row in contrasts} == set(sources)
    capture = {
        "schema": "kit.sw2026.principal-revolve-native-discovery-comparison.v1", "oracle_sha256": ORACLE,
        "oracle_version": ORACLE_VERSION, "source_revision": prep["source_revision"],
        "source_tree": prep["source_tree"], "inspection_sha256": report_sha, "preparation_sha256": prep_sha,
        "controls_healthy": True, "distinct_processes": 10, "sealed_sources_read": 0, "cases": contrasts,
        "compared_numeric_mass_fields": len(contrasts) * 3 * 6,
    }
    raw = (json.dumps(capture, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with output.open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"cases": len(contrasts), "receipt_sha256": sha256(raw).hexdigest()}))


if __name__ == "__main__":
    parser = ArgumentParser()
    for name in ("generated", "disclosed", "right", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    main(args.generated, args.disclosed, args.right, args.output)
