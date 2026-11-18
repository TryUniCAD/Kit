from argparse import ArgumentParser
from pathlib import Path
import json
import os

from AuthorCurves import digest, require, write_json
from AuthorDocumentMassUnits import metadata, unit_state
from AuthorRectangleAnchors import CONTROL, ORACLE
from InspectFreecadBoxNative import TOOLS, control_phase, phase, snapshot


SCHEMA = "kit.sw2026.freecad-box-releases-native.v1"
METHODS = TOOLS | {"AuthorDocumentMassUnits.py", "DocumentUnitApi.py", "InspectFreecadBoxReleasesNative.py"}
CASES = ("Freecad102", "Freecad114")


def checked(root, path, expected):
    path = root / path
    require(path.is_file() and not path.is_symlink() and path.resolve(strict=True).is_relative_to(root)
            and digest(path) == expected, "FreeCAD releases native packet changed")
    return path


def verify(path, wanted):
    root = path.parent.resolve(strict=True)
    job = json.loads(checked(root, path.name, wanted).read_bytes())
    require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE
            and job["control_sha256"] == CONTROL and job["heldout_inputs_read"] == 0,
            "use the exact disclosed FreeCAD release packet")
    require(Path(__file__).resolve().parent == root / "Tools" and set(job["tools_sha256"]) == METHODS,
            "use the exact FreeCAD release observer tool closure")
    for name, expected in job["tools_sha256"].items():
        checked(root, Path("Tools") / name, expected)
    seed = checked(root, "Control.SLDPRT", CONTROL)
    api = json.loads(checked(root, "DocumentUnitApi.json", job["api_sha256"]).read_bytes())
    build = json.loads(checked(root, "BuildProof.json", job["build_proof_sha256"]).read_bytes())
    cases = job["cases"]
    require(tuple(case["id"] for case in cases) == CASES and build["guarded_workers"] == 19 and build["passed"],
            "FreeCAD release native cohort differs from the guarded source proof")
    for case in cases:
        source = checked(root, case["input"], case["sha256"])
        result = build["builds"][case["source_case"]]
        row = result["generated"]
        settings = result["normal_sdk_readback"]
        require(source.name == "F14a.SLDPRT" and source.stat().st_size == row["bytes"]
                and case["sha256"] == row["sha256"] == result["without_source_cache_sha256"]
                and row["runtime_input_file_reads"] == 0 and case["source_sha256"] == row["source_sha256"]
                and case["source_text"] == row["source_text"] and case["parameter_bindings"] == row["parameter_bindings"]
                and settings["archive_system_code"] == 3 and settings["archive_mass_code"] == 2
                and case["required_native_body_label"] == row["source_body_label"]
                and case["density_kg_m3"] == 1 and case["document_preference_density_kg_m3"] == 1000,
                "FreeCAD release native case does not match its generated model and expected owners")
        require([case["dimensions_m"][name] * 1000 for name in case["parameter_names"]] == row["source_dimensions_mm"],
                "FreeCAD native case sizes differ from its actual neutral dimensions")
    return root, job, seed, api


def run(path, wanted):
    require(os.name == "nt", "FreeCAD release candidate measurement requires the pinned Windows oracle")
    root, job, seed, api = verify(path, wanted)
    require(metadata() == api, "registered native unit API differs from the preparation packet")
    output = root / "Inspection"
    output.mkdir(exist_ok=False)
    rows = {}
    result = {"schema": SCHEMA, "packet_sha256": wanted, "phases": rows, "passed": False,
              "native_material_assignment_qualified": False, "complete_original_corpus_conversions": 0,
              "heldout_inputs_read": 0}

    def add(name, state):
        rows[name] = state
        write_json(output / "Result.json", result)

    def with_units(author, case):
        state = snapshot(author, case)
        units = unit_state(author, api)
        values = api["enums"]
        require(units["swUnitSystem"] == values["swUnitSystem_e"]["swUnitSystem_Custom"]
                and units["swUnitsLinear"] == values["swLengthUnit_e"]["swMM"]
                and units["swUnitsAngular"] == values["swAngleUnit_e"]["swDEGREES"]
                and units["swUnitsMassPropMass"] == values["swUnitsMassPropMass_e"]["swUnitsMassPropMass_Kilograms"],
                "FreeCAD release box lost its native millimetre or kilogram setting")
        return state | {"document_units": units}

    try:
        add("ControlBefore", control_phase(output, "ControlBefore", seed))
        if rows["ControlBefore"]["passed"]:
            for case in job["cases"]:
                directory = output / case["id"]
                directory.mkdir()
                source = checked(root, case["input"], case["sha256"])
                generated = phase(directory, "Generated", source, case["sha256"], case, observe_snapshot=with_units)
                add(case["id"] + "/Generated", generated)
                if generated["passed"]:
                    reopened = phase(directory, "FreshReopen", directory / "Generated" / "Edited.SLDPRT",
                                     generated["saved_sha256"], case, prior=generated, observe_snapshot=with_units)
                    add(case["id"] + "/FreshReopen", reopened)
    finally:
        add("ControlAfter", control_phase(output, "ControlAfter", seed))
    verify(path, wanted)
    native_ids = [(row["oracle_identity"]["process_id"], row["oracle_identity"]["process_creation_filetime"])
                  for row in rows.values() if row.get("oracle_identity")]
    result["controls_healthy"] = all(rows[role]["passed"] for role in ("ControlBefore", "ControlAfter"))
    result["distinct_native_processes"] = len(set(native_ids))
    result["passed"] = len(set(native_ids)) == len(rows) == 6 and all(row["passed"] for row in rows.values())
    write_json(output / "Result.json", result)
    return result


if __name__ == "__main__":
    parser = ArgumentParser(description="Measure the generated FreeCAD 1.0 and 1.1 origin box variants")
    parser.add_argument("action", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    if args.action == "verify":
        root, _, _, _ = verify(args.packet, args.packet_sha256)
        require(not (root / "Inspection").exists(), "FreeCAD release native packet output is already in use")
        print(json.dumps({"passed": True, "processes_started": 0, "heldout_inputs_read": 0}))
    else:
        result = run(args.packet, args.packet_sha256)
        print(json.dumps({"passed": result["passed"], "processes": result["distinct_native_processes"]}))
        raise SystemExit(0 if result["passed"] else 3)
