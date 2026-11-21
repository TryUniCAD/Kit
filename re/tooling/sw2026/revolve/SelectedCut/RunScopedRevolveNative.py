from argparse import ArgumentParser
from math import tau
from pathlib import Path, PureWindowsPath
import json
import os
import re
import sys

HERE = Path(__file__).resolve()
sys.path[:0] = [str(HERE.parent), str(HERE.parents[2])]

from RevolveFamilyModel import STOCK_NAMES, edited_case, validate_specs
from RunStockCutSelector import (
    CONTROL_SHA, ORACLE_SHA, checked, encode, observe_factory, publish, require,
    TOOLS as SELECTOR_TOOLS,
)


SCHEMA = "kit.sw2026.scoped-revolve-candidate-packet.v1"
TOOLS = (HERE.name, *SELECTOR_TOOLS)
PREFIX = PureWindowsPath(r"C:\KitSdkCandidates")
CONTROL = "Control/RevolveFull.SLDPRT"
MODEL = "ModelSpecs.json"


def path_for(case, suffix=""):
    return case["name"] + suffix + ".SLDPRT"


def verify(path, pin):
    root = path.parent
    data = json.loads(checked(path, pin))
    guest = PureWindowsPath(data["guest_workspace"])
    locator = PureWindowsPath(data["guest_packet"])
    require(data["schema"] == SCHEMA and data["oracle_sha256"] == ORACLE_SHA
            and re.fullmatch(r"[a-f0-9]{40}", data["codec_revision"])
            and re.fullmatch(r"[a-f0-9]{40}", data["codec_src_tree"])
            and guest.parent == PREFIX and guest.is_absolute()
            and locator.name == root.name and locator.is_absolute()
            and data["new_heldout_credit"] == data["runtime_reads"] == 0,
            "invalid disclosed selected-revolve packet or output location")
    if os.name == "nt":
        require(path.resolve() == (Path(locator) / "Packet.json").resolve()
                and HERE == (root / "Tools" / HERE.name).resolve(),
                "guest packet and runner location differ from frozen transport")
    files = data["files"]
    cases = validate_specs(json.loads(checked(root / MODEL, files[MODEL])))
    expected = {CONTROL, MODEL, *(f"Tools/{name}" for name in TOOLS),
                *(f"Candidates/{path_for(case)}" for case in cases)}
    require(set(files) == expected and files[CONTROL] == CONTROL_SHA
            and all(case["split"] == "discovery" and case["family"] == "cut"
                    and not case["reverse"] and case["scope"] in ("inner", "outer")
                    for case in cases)
            and set(data["construction"]) == {case["name"] for case in cases},
            "packet contains unqualified cases or an unexpected file")
    for name, digest in files.items():
        checked(root / name, digest)
    for case in cases:
        item = data["construction"][case["name"]]
        target = f"Candidates/{path_for(case)}"
        require(item["sha256"] == files[target] and item["zero_runtime_reads"]
                and item["selector"]["f108"] == -1 and item["selector"]["ff0"] is None
                and len(item["streams"]) == 10,
                "candidate output or typed proof differs")
    return data, cases


def stock_roles(state, title):
    drivers = state["stock_drivers"]
    require(set(drivers) == set(STOCK_NAMES), "actual stock driver names are incomplete")
    result = {}
    for owner, item in drivers.items():
        require(item["name"] == f"D1@{owner}@{title}.Part" and item["radians"] == tau
                and len(item["parents"]) == 2, "a stock driver lost its actual owner")
        result[owner] = item["parents"], item["radians"]
    return result


def native_trial(path, pin):
    import Swapp
    from AuthorRevolveFamilies import constants_from_registration
    from AuthorRevolveSources import run_phase
    from InspectFresh import healthy, inspect

    data, cases = verify(path, pin)
    root = path.parent
    inspection = root / "Inspection"
    workspace = Path(data["guest_workspace"])
    require(os.name == "nt" and not workspace.exists() and not inspection.exists(),
            "native evaluation needs fresh guest work and inspection paths")

    def idle():
        return not Swapp.application_pids() and not Swapp.owned_process_ids()

    require(idle(), "an existing SOLIDWORKS process owns the oracle")
    observer = observe_factory(Swapp, constants_from_registration(Swapp))
    workspace.mkdir()
    inspection.mkdir()
    births = []
    result = {"schema": SCHEMA, "packet_sha256": pin, "oracle_sha256": ORACLE_SHA,
              "codec_revision": data["codec_revision"], "cases": {},
              "new_heldout_credit": 0, "public_writer": False}

    def remember(phase):
        identity = phase.get("oracle_identity")
        if identity:
            require(identity["version_matches"] and identity["file_version"] == "34.5.2.0604"
                    and identity["sha256"] == ORACLE_SHA, "native process differs from exact build")
            births.append(identity["process_creation_filetime"])

    def control(label):
        require(idle(), "the previous SOLIDWORKS process is still active")
        phase = inspect(root / CONTROL)
        digest = publish(inspection / f"{label}.json", encode(phase))
        remember(phase)
        return {"sha256": digest, "passed": healthy(phase) and phase["sha256"] == CONTROL_SHA}

    def inspect_case(case):
        require(idle(), "the previous case still owns the oracle")
        name = case["name"]
        location = inspection / name
        location.mkdir()
        filename = path_for(case)
        target = workspace / filename
        derivative = workspace / path_for(case, "-edited")
        file_key = f"Candidates/{filename}"
        pin_value = data["files"][file_key]
        publish(target, checked(root / file_key, pin_value))
        checks = []
        case_result = {"passed": False, "candidate_sha256": pin_value, "phases": checks}
        result["cases"][name] = case_result
        first, first_digest = run_phase(
            case, "reopen", target, ORACLE_SHA, pin_value, inspect_before_rebuild=True,
            record_path=location / "Initial.json", save_edited=derivative, author_type=observer,
        )
        remember(first)
        checks.append({"sha256": first_digest, "passed": first["passed"],
                       "open": first.get("open_status"), "failure": first.get("first_failure")})
        if first["passed"] and first.get("edit", {}).get("passed") and first.get("edited_derivative"):
            require(idle(), "SOLIDWORKS is still running before the fresh reopen")
            saved = first["edited_derivative"]
            last, last_digest = run_phase(
                edited_case(case), "edited-reopen", derivative, ORACLE_SHA, saved["sha256"],
                inspect_before_rebuild=True, record_path=location / "FreshReopen.json", author_type=observer,
            )
            remember(last)
            checks.append({"sha256": last_digest, "passed": last["passed"],
                           "open": last.get("open_status"), "failure": last.get("first_failure")})
            case_result["saved_sha256"] = publish(location / "Saved.SLDPRT", checked(derivative, saved["sha256"]))
            if last["passed"]:
                states = first["reopened"], first["edited"], last["reopened"]
                roles = tuple(stock_roles(state, title) for state, title in
                              zip(states, (name, name, name + "-edited"), strict=True))
                require(roles[0] == roles[1] == roles[2]
                        and all(state["features"] == states[0]["features"] and state["parents"] == states[0]["parents"]
                                for state in states)
                        and all(phase["open_status"] == {"opened": True, "errors": 0, "warnings": 0}
                                and phase["before_explicit_rebuild"]["bodies"] == 2
                                and phase["before_explicit_rebuild"]["whats_wrong"] == 0 for phase in (first, last))
                        and saved["save_status"] == [True, 0, 0],
                        "native saved copy changed the feature tree, drivers, or cold bodies")
                case_result.update(passed=True, tree_rows=len(states[0]["features"]),
                                   geometry_checks=sum(sum(row["passed"] for row in phase["checks"])
                                                       for phase in (first, last)))
        checked(target, pin_value)
        require(idle(), "the case did not release its SOLIDWORKS process")

    try:
        result["before"] = control("ControlBefore")
        if result["before"]["passed"]:
            for case in cases:
                inspect_case(case)
    except Exception as exc:
        result["batch_failure"] = repr(exc)
    finally:
        try:
            result["after"] = control("ControlAfter")
        except Exception as exc:
            result["after"] = {"passed": False, "failure": repr(exc)}
        result["idle_after"] = idle()
        result["distinct_processes"] = len(set(births))
        result["controls_healthy"] = bool(result.get("before", {}).get("passed") and result["after"]["passed"]
                                          and births == sorted(set(births)))
        result["passed"] = bool(result["controls_healthy"] and result["idle_after"]
                                and len(births) == 2 + 2 * len(cases) and not result.get("batch_failure")
                                and len(result["cases"]) == len(cases)
                                and all(row["passed"] for row in result["cases"].values()))
        verify(path, pin)
        digest = publish(inspection / "Result.json", encode(result))
        print(json.dumps({key: result[key] for key in ("passed", "controls_healthy", "distinct_processes")}
                         | {"sha256": digest}))
    return int(not result["passed"])


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("action", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--pin", required=True)
    args = parser.parse_args()
    if args.action == "run":
        sys.exit(native_trial(args.packet, args.pin))
    data, cases = verify(args.packet, args.pin)
    print(json.dumps({"sha256": args.pin, "verified_cases": len(cases)}))
