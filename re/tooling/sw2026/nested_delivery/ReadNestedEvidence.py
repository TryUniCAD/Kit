from hashlib import sha256
from pathlib import PureWindowsPath
import json

from NestedRequest import checked
from NestedWriteAudit import require
from ProveNestedDelivery import CASES


TERMINALS = {
    "SdkNestedNeutralNative03": "bcc4e421981553c488cf4638e50342ae74c65544f60cee265493fd464eb016e8",
    "SdkRepeatedNeutralNative03": "9dfda9928f350c7b4a4e4a8b4455dff1712ab30c34fbb403b75671b080b4d0a1",
    "SdkNestedDimensionedNative01": "84f8131b7a0745421f6e6a5ffd2bf91c9f2ec3d1e71f2a6b7b2358e7965e3340",
    "SdkRepeatedDimensionedNative01": "56488ff40ac32117973029686d57bc7090cb01f136fde4be7407ad386e7d0455",
}
ORACLE = {
    "build": "34.5.2.0604",
    "product": "SOLIDWORKS 2026 SP05.2",
    "sha256": "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe",
}
PHASES = ("before", "generated", "reopen", "after")


def read(directory, name, expected):
    return json.loads(checked(directory / name, expected))


def phase_rows(folder, terminal, control):
    phases = terminal["phases"]
    require(tuple(row["mode"] for row in phases) == PHASES, "native bracket is incomplete")
    require(all(row["name"] == control and row["source_files_unchanged"] is True
                for row in (phases[0], phases[-1])), "native controls do not match their immutable source")
    result = []
    for row in phases:
        raw = read(folder, f'Inspection/{row["mode"]}/Record.json', row["record_sha256"])
        require(raw["passed"] is True and raw["result"] | {
            key: raw[key] for key in ("started_at", "finished_at")
        } | {"record_sha256": row["record_sha256"]} == row, "terminal phase differs from its pinned native observation")
        identity = row["oracle_identity"]
        require(row["passed"] is True and identity["version_matches"] is True
                and (identity["file_version"], identity["sha256"]) == (ORACLE["build"], ORACLE["sha256"])
                and row["open_errors"] == row["open_warnings"] == 0
                and not row["dialogs"] and not row["controller_diagnostics"],
                "native phase has an unqualified oracle or document diagnostic")
        result.append({
            **{key: row[key] for key in ("mode", "passed", "started_at", "finished_at", "record_sha256", "open_errors", "open_warnings")},
            **{key: identity[key] for key in ("process_id", "process_creation_filetime")},
        })
    require(len({(row["process_id"], row["process_creation_filetime"]) for row in result}) == terminal["distinct_processes"] == 4
            and all(left["finished_at"] <= right["started_at"] for left, right in zip(result, result[1:])),
            "native observations do not form four chronologically distinct lifetimes")
    return result


def check_builds(folder, fixture):
    builds = [read(folder, name + ".stdout", fixture["build_sha256"][name]) for name in ("BuildA", "BuildB")]
    require(builds[0]["worker_pid"] != builds[1]["worker_pid"] and all(
        value["passed"] is True and value["runtime_input_file_reads"] == value["sdk_runtime_research_imports"] == 0
        and set(value["documents"]) == set(fixture["files"]) for value in builds
    ), "prior independent model-only builds are incomplete")
    for key, row in fixture["files"].items():
        require(all(
            (build["documents"][key]["sha256"], build["documents"][key]["bytes"], build["documents"][key]["native_path"])
            == (row["sha256"], row["bytes"], row["encoded_path"]) for build in builds
        ), "the fixture does not bind both independent builds")


def scene_members(root, state):
    files = state["definitions"]
    direct = {}

    def walk(owner, rows):
        children = [row["target"] for row in rows]
        require(direct.setdefault(owner, children) == children, "two occurrences disagree on their shared definition")
        for row in rows:
            target = row["target"]
            require(row["fixed"] is False and row["body_count"] > 0
                    and row["configuration"] == files[target]["configuration"],
                    "native occurrence did not resolve its expected active definition")
            walk(target, row["children"])

    walk(root, state["occurrences"])
    require(set(direct) == set(files) and state["direct_occurrences"] == len(direct[root])
            and state["body_count"] > 0 and all(row["tree"] and row["whats_wrong"] == 0 for row in files.values()),
            "native scene has an incomplete or unclean definition closure")
    return direct


def native_members(root, terminal, fixture, prediction):
    generated, reopen = terminal["phases"][1:3]
    initial = generated["initial"]
    direct = scene_members(root, initial)
    cold = fixture["files"]
    saved = generated["saved_files"]
    order = prediction["save_order"]
    require(set(order) == set(cold) == set(saved) and len(order) == len(cold) and order[-1] == root
            and all(order.index(child) < order.index(parent) for parent, rows in direct.items() for child in rows),
            "the native save order does not close the complete measured dependency graph")
    for state, identities in ((initial, cold), (generated["rebuilt"], cold), (generated["edited"], cold),
                              (reopen["initial"], saved), (reopen["rebuilt"], saved)):
        require(scene_members(root, state) == direct, "native rebuild or reopen changed the measured graph")
        require(all(
            row["sha256"] == identities[key]["sha256"] and row["file"] == cold[key]["file"]
            and row["configuration"] == initial["definitions"][key]["configuration"]
            for key, row in state["definitions"].items()
        ), "a measured lifecycle state does not own the frozen or synchronized file set")
    edit = prediction["edit"]
    require(all(row["status"] == [True, 0, 0] for row in saved.values())
            and initial["definitions"][edit["part"]]["parameters_m"][edit["parameter"]]
            != generated["edited"]["definitions"][edit["part"]]["parameters_m"][edit["parameter"]]
            and initial["definitions"][root]["mass_properties"]["volume"] != generated["edited"]["definitions"][root]["mass_properties"]["volume"],
            "the native driving edit and complete synchronized save are missing")
    return [{
        "id": key, "name": cold[key]["file"], "bytes": cold[key]["bytes"], "sha256": cold[key]["sha256"],
        "configuration": initial["definitions"][key]["configuration"], "children": direct[key],
    } for key in order]


def measured_request(workspace, case):
    folder = workspace / case
    packet = read(folder, "Packet.json", CASES[case])
    fixture = read(folder, "Fixture.json", packet["fixture_sha256"])
    request = read(folder, "NeutralRequest.json", fixture["request_sha256"])
    prediction = read(folder, "Prediction.json", fixture["prediction_sha256"])
    terminal = read(folder, "Inspection/Result.json", TERMINALS[case])
    require(terminal["packet_sha256"] == CASES[case] and terminal["fixture_sha256"] == packet["fixture_sha256"]
            and terminal["prediction_sha256"] == fixture["prediction_sha256"]
            and terminal["oracle_sha256"] == packet["oracle_sha256"] == ORACLE["sha256"]
            and terminal["heldout_inputs_read"] == packet["heldout_inputs_read"] == 0
            and terminal["source_lock_sha256"] == packet["source_lock_sha256"]
            and all(terminal[key] is True for key in ("passed", "controls_healthy", "bracket_order_verified",
                                                     "frozen_inputs_unchanged", "synchronized_derivative_files_match")),
            "native terminal does not qualify the exact disclosed packet and fixture")
    check_builds(folder, fixture)
    root = request["root"]
    require(root == terminal["root"] == prediction["root"], "native terminal has another root owner")
    (root_request,) = [row["request"] for row in request["definitions"] if row["id"] == root and row["kind"] == "assembly"]
    output = root_request["output"]
    native_path = PureWindowsPath(output["path_name"])
    require(str(native_path) == fixture["files"][root]["encoded_path"]
            and all(str(native_path.parent / row["file"]) == row["encoded_path"] for row in fixture["files"].values()),
            "native measured members do not share the actual canonical root namespace")
    members = native_members(root, terminal, fixture, prediction)
    epoch = output["saved_at"]
    return request, {
        "written_at": epoch,
        "receipt": {
            "schema": "kit.sw2026.rigid-nested-measurement.v1",
            "oracle": ORACLE,
            "packet_sha256": CASES[case], "fixture_sha256": packet["fixture_sha256"],
            "native_result_sha256": TERMINALS[case],
            "root": root, "namespace": str(native_path.parent), "written_at": epoch,
            "passed": True, "controls_healthy": True, "members": members,
            "phases": phase_rows(folder, terminal, packet["control"]),
        },
    }
