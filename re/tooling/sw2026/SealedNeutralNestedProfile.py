import json
from dataclasses import replace
from pathlib import PureWindowsPath

from AuthorCurves import require
from NestedAssemblySourcePlan import HEIGHT, ORACLE, WIDTH, checked, placement_matrix, validate_case
from SealedNestedAssemblyPlan import occurrence_names


PROFILE = "neutral_dimensioned_rectangle"
EVIDENCE_ROLES = ("Single", "Repeated")
EVIDENCE_FILES = ("Packet.json", "Fixture.json", "SourceManifest.json", "Prediction.json", "Result.json")
WORKER = "re/tooling/sw2026/AuditNestedNeutralComposition.py"


def read_evidence(folder, pins, revision, sdk_tree, source_lock):
    require(set(pins) == set(EVIDENCE_FILES), "neutral discovery requires its complete evidence links")
    packet, fixture, source, prediction, result = (
        json.loads(checked(folder / name, pins[name], folder).read_bytes()) for name in EVIDENCE_FILES
    )
    require(result["passed"] and result["controls_healthy"] and result["distinct_processes"] == 4
            and result["bracket_order_verified"] and result["frozen_inputs_unchanged"]
            and result["synchronized_derivative_files_match"] and result["heldout_inputs_read"] == 0
            and result["oracle_sha256"] == ORACLE and result["source_lock_sha256"] == source_lock
            and packet["source_lock_sha256"] == source_lock
            and result["packet_sha256"] == pins["Packet.json"]
            and result["fixture_sha256"] == packet["fixture_sha256"] == pins["Fixture.json"]
            and result["source_manifest_sha256"] == fixture["source_manifest_sha256"] == pins["SourceManifest.json"]
            and result["prediction_sha256"] == fixture["prediction_sha256"] == pins["Prediction.json"]
            and source["revision"] == fixture["neutral_preparation_revision"] == revision and source["sdk_tree"] == sdk_tree,
            "sealed neutral evaluation requires a passed complete dimensioned trial on the exact writer revision")
    rows = result["phases"]
    require([row["mode"] for row in rows] == ["before", "generated", "reopen", "after"]
            and all(row["passed"] and row["oracle_identity"]["sha256"] == ORACLE
                    and row["open_errors"] == row["open_warnings"] == 0 for row in rows)
            and len({row["oracle_identity"]["process_creation_filetime"] for row in rows}) == 4,
            "neutral discovery phases or native identities are incomplete")
    leaves = {key: row for key, row in prediction["definitions"].items() if row["kind"] == "part"}
    require(bool(leaves) and all(
        len(row["initial"]["parameters_m"]) == 3 and all(
            value is not None and value > 0 for value in row["initial"]["parameters_m"].values()
        ) for row in leaves.values()
    ), "sealed neutral evaluation requires actual dimensioned leaves")
    for phase, stage, expected in ((rows[1], "initial", "initial"), (rows[1], "edited", "edited"), (rows[2], "initial", "edited")):
        for key, row in leaves.items():
            actual = phase[stage]["definitions"][key]
            target = row[expected]["parameters_m"]
            require(actual["whats_wrong"] == 0 and set(actual["parameters_m"]) == set(target)
                    and all(abs(actual["parameters_m"][name] - value) <= 1e-12 for name, value in target.items()),
                    "neutral discovery dimensions differ from the prepared editable targets")
    return {"worker_sha256": source["tool_sha256"][WORKER],
            "processes": [row["oracle_identity"]["process_creation_filetime"] for row in rows],
            "expanded": prediction["initial"]["expanded_occurrences"], "leaves": len(leaves)}


def source_request(case, working):
    from AuthorNestedRectangle import dimension_rectangle
    from interchange.serialization.EncodeData import ToData
    from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import MakePlainDoc

    validate_case(case)
    working = PureWindowsPath(working)
    require(working.is_absolute() and not working.drive.startswith("\\\\") and ".." not in working.parts,
            "private neutral assembly paths must remain on the owned fixed guest disk")
    saved_at = 1794700051
    definitions = []
    for row in case["parts"]:
        name = row["name"]
        plain = MakePlainDoc(name, WIDTH * 1000, HEIGHT * 1000, row["depth_m"] * 1000)
        config, = plain.configurations
        plain = replace(plain, configurations=(replace(config, name="Default"),))
        definitions.append({"id": name, "kind": "part", "request": {
            "document": ToData(dimension_rectangle(plain)),
            "settings": {"output": {"path_name": str(working / (name + ".SLDPRT")), "saved_at": saved_at}},
        }})
    for assembly in case["assemblies"]:
        name = assembly["name"]
        occurrences = []
        for row, label in zip(assembly["occurrences"], occurrence_names(assembly["occurrences"]), strict=True):
            pose = placement_matrix(row["placement"])
            occurrences.append({"target": row["target"], "occurrence": {
                "name": label, "origin": pose[9:12], "u": pose[:3], "v": pose[3:6],
            }})
        definitions.append({"id": name, "kind": "assembly", "occurrences": occurrences, "request": {
            "name": name, "configuration_name": "Default",
            "system": {"planes": {"x": "Right Plane", "y": "Top Plane", "z": "Front Plane"}},
            "output": {"path_name": str(working / (name + ".SLDASM")), "saved_at": saved_at},
        }})
    return {"root": case["assemblies"][-1]["name"], "definitions": definitions}


def guarded_bundle(report, request):
    paths = {row["id"]: PureWindowsPath(
        (row["request"] if row["kind"] == "assembly" else row["request"]["settings"])["output"]["path_name"]
    ) for row in request["definitions"]}
    require(report["passed"] is True and report["runtime_file_reads"] == 0
            and report["root"] == paths[request["root"]].name
            and set(report["outputs"]) == {path.name for path in paths.values()},
            "sealed neutral guard evidence does not cover the complete generated bundle")
    documents = {key: report["outputs"][path.name] for key, path in paths.items()}
    require(all(PureWindowsPath(documents[key]["native_path"]) == path for key, path in paths.items()),
            "guarded sealed bundle changed a native destination")
    return {"schema": "kit.sw2026.generated-nested-assembly-bundle.v1", "root": request["root"],
            "input_runtime_file_access_attempts": 0, "native_acceptance": False, "documents": documents,
            "worker_pid": report["worker_pid"]}
