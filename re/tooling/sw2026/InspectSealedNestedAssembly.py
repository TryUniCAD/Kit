from __future__ import annotations

import json
import time
from shutil import copyfile

from AuthorCurves import digest, require, write_json
from AuthorNestedAssemblySources import edit_depth, force_rebuild, save_current
from InspectGeneratedNestedAssembly import definition_order, observe_scene
from NestedAssemblySourcePlan import ORACLE, checked
from RunSealedNestedSourcePhase import PrivateRecorder, opaque_identity, value_hash


def floating_occurrences(rows):
    return all(row["fixed"] is False and floating_occurrences(row["children"]) for row in rows)


def measure(phase, private, files, bundle, prediction, raw, publish, prior=None):
    import Swapp
    from AuthorCurves import CurveAuthor
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity

    working = private / "GeneratedInput"
    paths = {name: working / row["file"] for name, row in files.items()}
    recorder = PrivateRecorder(raw, {"phase": phase}, publish)
    result = {"passed": False, "mode": phase}
    controller = None
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("verify idle oracle", Swapp.sweep)
            if phase == "generated":
                working.mkdir(exist_ok=False)
                for row in files.values():
                    source = checked(private / "FrozenGenerated" / row["file"], row["sha256"], private)
                    copyfile(source, working / row["file"])
                require(all(digest(paths[name]) == row["sha256"] for name, row in files.items()), "sealed working files differ from the frozen writer outputs")
                saved = None
            else:
                source = checked(private / "generated/1/Private.json", prior["private_record_sha256"], private)
                previous = json.loads(source.read_bytes())
                require(previous["passed"] is True, "sealed native save phase did not pass")
                saved = previous["result"]["saved_files"]
                require(set(saved) == set(paths) and all(digest(paths[name]) == row["sha256"] for name, row in saved.items()), "sealed saved dependencies changed before reopen")
            publish(stage="starting_oracle")
            controller = recorder.call("launch fresh owned oracle", Swapp.Sw)
            identity = recorder.call("verify executable version and SHA-256", application_identity, controller.app)
            require(identity["version_matches"] and identity["sha256"] == ORACLE and controller.revision == "34.5.2", "unexpected native build")
            result["oracle_identity"] = identity
            publish(stage="native_work", identity=opaque_identity(identity))
            author = CurveAuthor(controller.app, recorder, Swapp)
            root, errors, warnings = recorder.call("open exact generated nested root without preloading children", controller.open,
                                                  paths[prediction["root"]], read_only=phase == "reopen")
            result.update(open_errors=errors, open_warnings=warnings)
            require(root is not None and errors == warnings == 0, "sealed generated root failed or warned on open")
            edited = phase == "reopen"
            result["initial"], loaded = observe_scene(author, root, paths, prediction, edited)
            require(floating_occurrences(result["initial"]["occurrences"]), "sealed generated hierarchy changed ordinary floating occurrence semantics")
            order = definition_order(bundle)
            for name in order:
                force_rebuild(author, loaded[name])
            result["rebuilt"], loaded = observe_scene(author, root, paths, prediction, edited)
            if phase == "generated":
                edit = prediction["edit"]
                edit_depth(author, loaded[edit["part"]], edit["depth_m"])
                for name in order:
                    force_rebuild(author, loaded[name])
                result["edited"], loaded = observe_scene(author, root, paths, prediction, True)
                require(result["initial"]["definitions"][prediction["root"]]["mass_properties"]["volume"] !=
                        result["edited"]["definitions"][prediction["root"]]["mass_properties"]["volume"], "sealed driving depth edit did not change the expanded root")
                saved = result["saved_files"] = {}
                for name in order:
                    saved[name] = save_current(author, loaded[name], paths[name], working)
                    require(all(digest(paths[earlier]) == row["sha256"] and int(author.get(loaded[earlier], "GetUpdateStamp")) == row["update_stamp"]
                                for earlier, row in saved.items()), "sealed owner save changed an already synchronized dependency")
                write_json(private / "SavedState.json", {"files": saved, "edited_depth_m": edit["depth_m"]})
            else:
                require(all(result["initial"]["definitions"][name]["update_stamp"] == row["update_stamp"] for name, row in saved.items()),
                        "sealed fresh reopen bound different persisted update stamps")
                original = previous["result"]["edited"]["definitions"]
                require(all(row["tree"] == original[name]["tree"] for name, row in result["initial"]["definitions"].items()),
                        "sealed edited definition trees changed after save and fresh reopen")
            require(all(digest(paths[name]) == row["sha256"] for name, row in saved.items()), "sealed generated file state changed after measurement")
            result["saved_artifact_manifest_sha256"] = value_hash({files[name]["file"]: {"sha256": row["sha256"], "bytes": row["bytes"]} for name, row in saved.items()})
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["exception"] = repr(error)
        finally:
            if controller is not None:
                publish(stage="closing_oracle")
                controller.close()
                result["controller_diagnostics"] = controller.diagnostics
    result["dialogs"], result["progress_windows"] = monitor.log, monitor.progress
    result["passed"] = bool(result["passed"] and not result["dialogs"] and not result.get("controller_diagnostics") and not recorder.data["cleanup_errors"])
    recorder.data.update(result=result, passed=result["passed"], finished_at=time.time())
    recorder.flush()
    require(result["passed"], "sealed native phase failed; detailed evidence remains guest-private")
    return {"identity": opaque_identity(result["oracle_identity"]), "saved_artifact_manifest_sha256": result["saved_artifact_manifest_sha256"]}
