from argparse import ArgumentParser
from hashlib import sha256
from math import isclose, pi
from pathlib import Path
import json
import os


ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"
SOURCES = {
    "H01TranslatedDiameter": ("16837814717ae5a5c2a815b42afda8583b2cc51db4411b5837ca904ee8d5dddc",
                              0.007731, 0.0, 0.017293, (-0.013719, 0.029113)),
    "H05RotatedCapsule": ("f2ed589c9405bc81dc5d76b99ab469a2a14818ab0967cbb4a44128e5ea6b0662",
                          0.003713, 0.029173, 0.007139, (0.021371, -0.005193)),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def expected(radius, span, depth, center):
    area = pi * radius ** 2 + 2 * radius * span
    perimeter = 2 * pi * radius + 2 * span
    return {"volume": area * depth, "area": 2 * area + perimeter * depth,
            "com": (*center, depth / 2)}


def compare(measured, target):
    for name in ("volume", "area"):
        require(isclose(measured[name], target[name], rel_tol=2e-7, abs_tol=1e-15), "native " + name + " differs")
    require(all(isclose(a, b, rel_tol=2e-7, abs_tol=1e-12)
                for a, b in zip(measured["com"], target["com"], strict=True)), "native centroid differs")


def observe(path, checksum, target):
    import Swapp
    from OracleIdentity import application_identity

    require(digest(path) == checksum, "native read-only source differs from its lock")
    Swapp.sweep()
    with Swapp.Dismisser() as dialog:
        oracle = Swapp.Sw()
        try:
            picked = application_identity(oracle.app)
            require(picked["sha256"] == ORACLE and picked["version_matches"]
                    and picked["file_version"] == "34.5.2.0604", "unexpected native build")
            require(int(Swapp.cv(oracle.app, "GetDocumentCount")) == 0, "native phase must be cold")
            observed = Swapp.measure(oracle, path, read_only=True)
            require(observed["opened"] and observed["open_errors"] == observed["open_warnings"] == 0
                    and observed["rebuilt"] and observed["whats_wrong"] == 0 and observed["bodies"] == 1
                    and not observed["session_diagnostics"], "native open, rebuild or body inventory differs")
            require(all(row.get("error") == 0 and row.get("warning") is False for row in observed["features"]),
                    "native feature tree has diagnostics")
            values = {name: observed["mass"][name] for name in ("volume", "area", "com")}
            if target is not None:
                compare(values, target)
        finally:
            oracle.close()
    require(not dialog.log and not oracle.diagnostics and digest(path) == checksum, "native source or session changed")
    return {"passed": True, "source_sha256": checksum, "geometry_si": values,
            "native_process_creation": picked["process_creation_filetime"], "body_count": 1,
            "zero_open_and_rebuild_diagnostics": True}


def run(root, control):
    require(os.name == "nt", "observe the locked curve sources inside the oracle")
    cases = [("ControlBefore", control, CONTROL, None)]
    for key, (checksum, radius, span, depth, center) in SOURCES.items():
        cases.append((key, root / key / (key + ".SLDPRT"), checksum, expected(radius, span, depth, center)))
    cases.append(("ControlAfter", control, CONTROL, None))
    rows = {}
    for key, locator, checksum, target in cases:
        if key in SOURCES and not rows["ControlBefore"]["passed"]:
            rows[key] = {"passed": False, "reason": "leading control failed"}
            continue
        try:
            rows[key] = observe(locator, checksum, target)
        except Exception as error:
            rows[key] = {"passed": False, "reason": str(error)}
    controls = rows["ControlBefore"]["passed"] and rows["ControlAfter"]["passed"]
    if controls:
        compare(rows["ControlBefore"]["geometry_si"], rows["ControlAfter"]["geometry_si"])
    processes = {row["native_process_creation"] for row in rows.values() if row["passed"]}
    return {"schema": "kit.sw2026.curved-fin-native-references.v1", "oracle_file_version": "34.5.2.0604",
            "oracle_sha256": ORACLE, "distinct_accepted_processes": len(processes), "controls_healthy": controls,
            "all_passed": controls and len(processes) == len(cases), "phases": rows}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("heldout_directory", type=Path)
    parser.add_argument("control", type=Path)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    observed = run(args.heldout_directory, args.control)
    with args.receipt.open("x", encoding="utf-8") as file:
        json.dump(observed, file, indent=2, sort_keys=True, allow_nan=False)
        file.write("\n")
    print(json.dumps({name: observed[name] for name in ("all_passed", "controls_healthy", "distinct_accepted_processes")}))
    raise SystemExit(0 if observed["all_passed"] else 1)
