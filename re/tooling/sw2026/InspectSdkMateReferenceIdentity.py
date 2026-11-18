from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
from shutil import copyfile
import sys


SCHEMA = "kit.sw2026.sdk-mate-specific-plane-diagnostic.v1"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    data = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with path.open("xb") as output:
        output.write(data)
    return hashlib.sha256(data).hexdigest()


def windows_path(path):
    return str(PureWindowsPath(r"\\Mac\Home") / path.resolve(strict=True).relative_to(Path.home()))


def host_path(value):
    return Path.home().joinpath(*PureWindowsPath(value).relative_to(PureWindowsPath(r"\\Mac\Home")).parts)


def base_values(packet, expected):
    if digest(packet) != expected:
        raise ValueError("the original immutable ordered packet differs")
    sys.path.insert(0, str(packet.parent / "Tools"))
    import InspectSdkOrderedMates

    return InspectSdkOrderedMates.verify(packet, expected)


def prepare(args):
    packet = args.base_packet.resolve(strict=True)
    _, _, paths, _, _, _, _ = base_values(packet, args.base_packet_sha256)
    for _, native, expected in paths.values():
        if digest(host_path(native)) != expected:
            raise ValueError("the no-save trial working files changed before the matched diagnostic")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    tools = output / "Tools"
    tools.mkdir()
    copied = tools / Path(__file__).name
    copyfile(Path(__file__), copied)
    job = {"schema": SCHEMA, "base_packet": {"host_path": str(packet), "windows_path": windows_path(packet), "sha256": args.base_packet_sha256},
           "observer_sha256": digest(copied), "native_storage_writes": False, "writer_output_count": 0, "heldout_inputs_read": 0,
           "purpose": "matched read-only specific-plane equality in native A22 and the unchanged fully SDK generated ordered pair"}
    sha = write(output / "Packet.json", job)
    recipe = {"verify": ["py", "-3.11", "-B", windows_path(copied), "verify", windows_path(output / "Packet.json"), "--packet-sha256", sha],
              "run": ["py", "-3.11", "-B", windows_path(copied), "run", windows_path(output / "Packet.json"), "--packet-sha256", sha],
              "result_windows_path": str(PureWindowsPath(windows_path(output / "Packet.json")).parent / "Inspection" / "Result.json")}
    recipe_sha = write(output / "Recipe.json", recipe)
    return {"packet": str(output / "Packet.json"), "packet_sha256": sha, "observer_sha256": job["observer_sha256"], "recipe_sha256": recipe_sha,
            "native_processes_started": 0, "heldout_inputs_read": 0}


def verify(packet, expected):
    if digest(packet) != expected:
        raise ValueError("the matched read-only diagnostic packet differs")
    job = json.loads(packet.read_bytes())
    if job["schema"] != SCHEMA or job["native_storage_writes"] is not False or job["writer_output_count"] != 0 or job["heldout_inputs_read"] != 0:
        raise ValueError("expected the no-storage disclosed equality diagnostic")
    if Path(__file__).resolve().parent != (packet.parent / "Tools").resolve() or digest(Path(__file__)) != job["observer_sha256"]:
        raise ValueError("the read-only diagnostic source differs")
    key = "windows_path" if os.name == "nt" else "host_path"
    values = base_values(Path(job["base_packet"][key]), job["base_packet"]["sha256"])
    for _, native, sha in values[2].values():
        actual = Path(native) if os.name == "nt" else host_path(native)
        if digest(actual) != sha:
            raise ValueError("the untouched generated working pair differs")
    return job, values


def reference_options(author, model, child, prediction, case):
    import Swapp
    from AssemblyMateEvidence import mate_features
    from InspectSdkSingleMate import observe

    if prediction is None:
        result = {"configurations": [str(author.get(author.get(doc, "GetActiveConfiguration"), "Name")) for doc in (model, child)]}
    else:
        result = observe(author, model, child, prediction)
    assembly = author.typed(model, "AssemblyDoc")
    components = {str(author.get(value, "Name2")): author.typed(value, "Component2") for value in author.get(assembly, "GetComponents", True)}
    rows = result["ordered_reference_diagnostics"] = []
    features = list(mate_features(author, model))
    if len(features) != len(case["mates"]) or len(components) != 2:
        raise ValueError("the matched reference diagnostic requires the complete ordinary group")
    for feature, request in zip(features, case["mates"], strict=True):
        mate = author.typed(author.get(feature, "GetSpecificFeature2"), "Mate2")
        row = {"mate": str(author.get(feature, "Name")), "kind": request["kind"], "entities": []}
        rows.append(row)
        for index, (_, datum) in enumerate(request["planes"]):
            entity = author.typed(author.get(mate, "MateEntity", index), "MateEntity2")
            component = author.typed(author.get(entity, "ReferenceComponent"), "Component2")
            name = str(author.get(component, "Name2"))
            reference = author.get(entity, "Reference")
            again = author.get(entity, "Reference")
            endpoint = {"occurrence": name, "datum": datum, "reference_type": int(author.get(entity, "ReferenceType2")), "comparisons": []}
            row["entities"].append(endpoint)
            endpoint["repeated_reference_equality"] = int(author.rec.call(
                "IsSame repeated mate reference", Swapp.invoke, author.app, "IsSame", reference, again,
                parameters={"mate": row["mate"], "endpoint": index, "occurrence": name, "datum": datum}))
            for candidate_name, candidate in components.items():
                named = author.get(candidate, "FeatureByName", datum)
                plane = author.get(named, "GetSpecificFeature2")
                repeated = author.get(named, "GetSpecificFeature2")
                values = {}
                for label, left, right in (("feature_equality", reference, named), ("specific_plane_equality", reference, plane),
                                           ("repeated_specific_plane_equality", plane, repeated)):
                    values[label] = int(author.rec.call(
                        "IsSame " + label, Swapp.invoke, author.app, "IsSame", left, right,
                        parameters={"mate": row["mate"], "endpoint": index, "actual_occurrence": name, "candidate_occurrence": candidate_name, "datum": datum}))
                endpoint["comparisons"].append({"candidate_occurrence": candidate_name, "expected_occurrence": candidate_name == name, **values})
    return result


def run(packet, expected):
    if os.name != "nt":
        raise ValueError("only the serial pinned Windows oracle can run this diagnostic")
    job, values = verify(packet, expected)
    _, prediction, paths, control, source, case, _ = values
    from InspectCombinedPlanarMates import phase, signature
    from AuthorCurves import write_json

    output = packet.parent / "Inspection"
    output.mkdir()
    phases = {}
    report = {"schema": SCHEMA, "packet_sha256": expected, "phases": phases, "native_storage_writes": False,
              "writer_output_count": 0, "heldout_inputs_read": 0, "native_acceptance": False, "passed": False}
    generated = {"case": case, "child_size_m": [prediction["child_dimensions_m"][key] for key in ("width", "height", "depth")]}
    targets = tuple(Path(paths[key][1]) for key in ("assembly", "child"))

    def record(role, selected, chosen_paths, wanted):
        def observe(author, model, child):
            return reference_options(author, model, child, wanted, selected["case"])

        row = phase(selected, selected["case"], role, *chosen_paths, output / role, observe=observe)
        phases[role] = row
        write_json(output / "Result.json", report)
        return row

    try:
        before = record("ControlBefore", control, source, None)
        if before["passed"]:
            record("Generated", generated, targets, prediction)
    finally:
        after = record("ControlAfter", control, source, None)
        verify(packet, expected)
        healthy = bool(phases.get("ControlBefore", {}).get("passed") and after["passed"])
        report["controls_healthy"] = healthy
        report["control_identity_preserved"] = bool(healthy and signature(phases["ControlBefore"]["rebuilt"]) == signature(after["rebuilt"]))
        births = {row["oracle_identity"]["process_creation_filetime"] for row in phases.values() if row.get("oracle_identity")}
        report.update(distinct_processes=len(births), immutable_inputs_unchanged=True)
        report["passed"] = bool(report["control_identity_preserved"] and len(phases) == len(births) == 3 and all(row["passed"] for row in phases.values()))
        write_json(output / "Result.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description="Observe component-context plane equality without native file writes")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--base-packet", type=Path, required=True)
    prepare_parser.add_argument("--base-packet-sha256", required=True)
    prepare_parser.add_argument("--output", type=Path, required=True)
    for command in ("verify", "run"):
        child = commands.add_parser(command)
        child.add_argument("packet", type=Path)
        child.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        report = prepare(args)
    elif args.command == "verify":
        verify(args.packet.resolve(strict=True), args.packet_sha256)
        forbidden = [name for name in sys.modules if name == "Swapp" or name == "pythoncom" or name.startswith("win32com")]
        if forbidden:
            raise ValueError("the matched host verifier imported COM")
        report = {"passed": True, "com_imports": forbidden, "native_processes_started": 0}
    else:
        report = run(args.packet.resolve(strict=True), args.packet_sha256)
    print(json.dumps(report if args.command != "run" else {key: report[key] for key in ("passed", "controls_healthy", "distinct_processes")}, sort_keys=True))
    return 0 if report.get("passed", True) else 3


if __name__ == "__main__":
    raise SystemExit(main())
