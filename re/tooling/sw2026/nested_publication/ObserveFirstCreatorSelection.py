from argparse import ArgumentParser
import json
import os
from pathlib import Path
import sys
from time import time

from ObserveFirstCreatorNative import (
    BUILD, CASES, MODES, ORACLE, checked, copy_new, digest, getter, publish, require, verify,
)


PACKET = "c8addf29032d630b2513ceae9f5d00a7bd5e0f56f578c619079d16bfe30a690f"
DIRECT = "8c75f9ed154166fef3dcb7421e62bacc72f8b46e189e60a8b2fff9f63fb52f61"
CONTROL = "236865bd1e13e246199429ad635da99a737b6280802c61df252c92d613275452"
LOCAL = r"C:\KitWarmFirstCreatorSelection"
LABELS = ("Before", *(f"{case}/{mode}" for case in CASES for mode in MODES), "After")


def body_count(author):
    part = author.typed(author.model, "PartDoc")
    return len(author.get(part, "GetBodies2", 0, False) or ())


def issues(author):
    return int(author.get(author.get(author.model, "Extension"), "GetWhatsWrongCount"))


def scope(author, definition, *, selected):
    result = {
        "feature_scope": getter(author, definition, "FeatureScope", "boolean"),
        "auto_select": getter(author, definition, "AutoSelect", "boolean"),
        "body_count": getter(author, definition, "GetFeatureScopeBodiesCount", "count"),
    }
    if selected:
        raw = author.get(definition, "FeatureScopeBodies")
        result["array_count"] = None if raw is None else len(raw)
    return result


def observe(label, folder, source, file_hash, feature, selected, control):
    from AuthorCurves import CurveAuthor, Recorder
    from OracleIdentity import application_identity
    import Swapp

    folder.mkdir(parents=True, exist_ok=False)
    recorder = Recorder(folder / "Record.json", {"phase": label, "input_sha256": file_hash})
    local = Path(LOCAL).joinpath(*label.split("/"), source.name)
    local.parent.mkdir(parents=True, exist_ok=False)
    copy_new(source, local, file_hash)
    result = {"passed": False, "input_sha256": file_hash, "started_at": time()}
    recorder.data["result"] = result
    controller = author = None
    with Swapp.Dismisser() as dialogs:
        try:
            recorder.call("guard the idle native application", Swapp.sweep)
            controller = recorder.call("start a fresh oracle", Swapp.Sw)
            identity = recorder.call("verify the installed oracle identity", application_identity, controller.app)
            result["oracle_identity"] = identity
            require(identity["sha256"] == ORACLE and identity["file_version"] == BUILD
                    and identity["version_matches"] and controller.revision == "34.5.2", "oracle identity changed")
            author = CurveAuthor(controller.app, recorder, Swapp)
            author.model, errors, warnings = recorder.call("open the immutable derivative", controller.open, local, read_only=True)
            result["open"] = [author.model is not None, errors, warnings]
            require(result["open"] == [True, 0, 0]
                    and Path(author.get(author.model, "GetPathName")).samefile(local), "wrong, failed or warned native open")
            active_count = 2 if control else 1
            require(author.get(author.model, "ForceRebuild3", False)
                    and issues(author) == 0 and body_count(author) == active_count, "initial rebuild or geometry failed")
            node = author.get(author.model, "FeatureByName", feature)
            require(node is not None and str(author.get(node, "Name")) == feature, "exact feature identity missing")
            result["feature_id"] = int(author.get(node, "GetID"))
            definition = author.typed(author.get(node, "GetDefinition"), "ExtrudeFeatureData2")
            result["direct"] = scope(author, definition, selected=selected)
            result["access_selections"] = bool(author.get(definition, "AccessSelections", author.model, Swapp.nothing()))
            require(result["access_selections"], "selection access refused on the exact feature")
            try:
                result["rollback_body_count"] = body_count(author)
                result["accessed"] = scope(author, definition, selected=selected)
            finally:
                author.get(definition, "ReleaseSelectionAccess")
                result["released"] = True
            require(author.get(author.model, "ForceRebuild3", False)
                    and issues(author) == 0 and body_count(author) == active_count, "selection release changed rebuilt geometry")
            result["observed_expected_scope"] = (
                result["accessed"]["feature_scope"] == {"status": "observed", "value": selected}
                and (not selected or result["accessed"]["auto_select"] == {"status": "observed", "value": False})
            )
            result["membership_available"] = (
                result["accessed"]["body_count"] == {"status": "observed", "value": int(control)}
                and result["accessed"].get("array_count") in ((1,) if control else (None, 0))
            )
            result["passed"] = result["observed_expected_scope"] and (
                result["membership_available"] if control else result["rollback_body_count"] == 0
            )
        except Exception as error:
            recorder.failure(error)
        finally:
            if controller is not None:
                try:
                    if author is not None and author.model is not None:
                        controller.close_doc(author.model)
                    controller.close()
                    Swapp.sweep()
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                result["controller_diagnostics"] = controller.diagnostics
    result.update(immutable=digest(local) == digest(source) == file_hash, finished_at=time(), dialogs=dialogs.log)
    result["passed"] &= bool(result["immutable"] and not result["dialogs"] and not result.get("controller_diagnostics")
                             and not recorder.data["first_failure"] and not recorder.data["cleanup_errors"])
    recorder.data["passed"] = result["passed"]
    recorder.flush()
    output = {**result, "record_sha256": digest(recorder.path)}
    print(json.dumps({"phase": label, "passed": output["passed"], "accessed": output.get("accessed")}), flush=True)
    return output


def main():
    parser = ArgumentParser(description="Observe first-creator scope within actual selection access")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--tool-sha256", required=True)
    args = parser.parse_args()
    require(os.name == "nt" and digest(Path(__file__)) == args.tool_sha256, "use the exact guest observer")
    root, job = verify(args.packet, PACKET)
    direct_path = root / "Native" / "Result.json"
    require(digest(direct_path) == DIRECT, "earlier native lifecycle receipt changed")
    direct = json.loads(direct_path.read_bytes())
    require(direct["all_native_lifecycles_passed"] and direct["controls_healthy"] and not direct["passed"],
            "selection contrast requires the exact incomplete direct getter comparison")
    sys.path.insert(0, str(root / "Tools"))
    control = root.parent / "GeneratedTwoStockGraph01" / "NativeAfterEdit.SLDPRT"
    require(digest(control) == CONTROL, "previously measured positive control changed")
    out = Path(__file__).resolve().parent / "Native"
    require(not Path(LOCAL).exists() and not out.exists(), "selection workspaces must be unused")
    Path(LOCAL).mkdir()
    out.mkdir()
    phases = {}
    for label in LABELS:
        if label in ("Before", "After"):
            source, pin, feature, selected = control, CONTROL, "ThroughFeature", True
        else:
            case, mode = label.split("/")
            name = CASES[case] + ".SLDPRT"
            row = direct["derivatives"][label]
            source = checked(root, row, f"Native/Derivatives/{case}/{mode}/{name}")
            pin, feature, selected = row["sha256"], job["cases"][case]["feature"], mode == "Selected"
        phases[label] = observe(label, out.joinpath(*label.split("/")), source, pin, feature, selected, label in ("Before", "After"))
    rows = tuple(phases.values())
    identities = {(row["oracle_identity"]["process_id"], row["oracle_identity"]["process_creation_filetime"])
                  for row in rows if "oracle_identity" in row}
    controls = phases["Before"]["passed"] and phases["After"]["passed"] and phases["Before"]["accessed"] == phases["After"]["accessed"]
    distinct = len(identities) == len(LABELS) and all(a["finished_at"] <= b["started_at"] for a, b in zip(rows, rows[1:]))
    memberships = all(phases[case + "/Selected"].get("membership_available") for case in CASES)
    result = {"schema": "kit.sw2026.first-creator-selection-access.v1", "packet_sha256": PACKET,
              "direct_result_sha256": DIRECT, "tool_sha256": args.tool_sha256, "phases": phases,
              "controls_healthy": controls, "distinct_native_processes": len(identities),
              "all_prior_body_lifecycles_passed": bool(controls and distinct and all(row["passed"] for row in rows)),
              "selected_memberships_confirmed": bool(controls and distinct and memberships),
              "heldout_inputs_read": 0, "public_writer_qualified": False}
    output_pin = publish(out / "Result.json", result)
    print(json.dumps({"result_sha256": output_pin, **{k: v for k, v in result.items() if k != "phases"}}))
    return int(not (result["all_prior_body_lifecycles_passed"] and result["selected_memberships_confirmed"]))


if __name__ == "__main__":
    sys.exit(main())
