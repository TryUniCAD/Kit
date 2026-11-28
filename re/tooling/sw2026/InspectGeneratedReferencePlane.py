from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))

from AuthorCurves import Recorder, digest, require, write_json


SCRIPT = Path(__file__).resolve()
SCHEMA = "kit.sw2026.generated-offset-plane-native-trial.v1"
SOURCE_LOCK_SHA256 = "c61560deff9c84addd65db48664ce6a5488ad3eecde9a070c62a215a5541d703"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
TOOLS = ("AuthorCurves.py", "AuthorAssemblySources.py", "AuthorReferencePlaneSources.py", "ReferencePlaneDimensions.py",
         "ReferencePlaneSourcePlan.py", "InspectCircleSketch.py", "InspectFresh.py", "ObserveAssemblyLoad.py",
         "OracleIdentity.py", "Swapp.py", SCRIPT.name)


def checked(path, sha, root):
    path = Path(path)
    require(path.resolve(strict=True).is_relative_to(root.resolve(strict=True)) and not path.is_symlink()
            and re.fullmatch(r"[0-9a-f]{64}", sha) and digest(path) == sha, "frozen plane input escaped custody or changed")
    return path


def predict(request, edit_distance_m):
    document = request["document"]
    plane = request["offset_plane_discovery"]
    axis = document["plane_axis"]
    require(axis in ("x", "y", "z") and document.get("profile_kind") == "circle" and document.get("feature_kind") == "blind_extrusion"
            and document["center_m"] == [0.0, 0.0] and document["circle_dimension"]["mode"] == "radius"
            and document["circle_dimension"]["fix_center"] is True, "native observer requires the admitted centered radius-driven blind cylinder")
    values = [plane["distance_m"], document["radius_m"], document["depth_m"], edit_distance_m]
    require(type(plane["reverse"]) is bool and all(type(value) in (float, int) and math.isfinite(value) and value > 1e-6 for value in values)
            and edit_distance_m != plane["distance_m"], "native prediction requires finite positive dimensions and an independent edit")
    normal = [float(index == "xyz".index(axis)) for index in range(3)]
    radius, depth = document["radius_m"], document["depth_m"]
    geometry = {}
    for role, distance in (("initial", plane["distance_m"]), ("edited", edit_distance_m)):
        origin = [(-distance if plane["reverse"] else distance) * value for value in normal]
        geometry[role] = {"distance_m": distance, "radius_m": radius, "depth_m": depth, "body_count": 1,
                          "volume": math.pi * radius * radius * depth, "area": 2 * math.pi * radius * (radius + depth),
                          "plane_origin": origin, "normal": normal,
                          "com": [a + b * depth / 2 for a, b in zip(origin, normal, strict=True)]}
    return {"name": document["name"], "configuration": document["configuration_name"], "plane": plane["name"],
            "sketch": document["sketch_name"], "boss": document["extrusion_name"], "origin": document["origin_name"],
            "principal_names": document.get("principal_names", request["presentation"]["plane_names"]),
            "base_axis": axis, "base_name": request["presentation"]["plane_names"][axis],
            "reverse": plane["reverse"], "geometry": geometry}


def verify(path, sha):
    root = path.parent.resolve(strict=True)
    job = json.loads(checked(path, sha, root).read_bytes())
    require(path.name == "Trial.json" and job["schema"] == SCHEMA and job["source_lock_sha256"] == SOURCE_LOCK_SHA256
            and job["oracle_sha256"] == ORACLE and job["heldout_inputs_tested"] == 0 and job["native_acceptance"] is False,
            "unexpected generated plane discovery provenance")
    require(SCRIPT.parent == root / "Tools" and set(job["tool_hashes"]) == set(TOOLS), "use the exact frozen plane observer")
    for name, expected in job["tool_hashes"].items():
        checked(root / "Tools" / name, expected, root / "Tools")
    checked(root / "SourceLock.json", SOURCE_LOCK_SHA256, root)
    manifest = json.loads(checked(root / "CodeManifest.json", job["code_manifest_sha256"], root).read_bytes())
    require(re.fullmatch(r"[0-9a-f]{40}", job["writer_revision"]) and all(manifest["files_sha256"].get(name) == expected
            for name, expected in job["writer_files_sha256"].items()), "writer revision or dependency manifest differs")
    checked(root / "ApiMetadata.json", job["api_metadata_sha256"], root)
    checked(root / "Request.json", job["generated"]["request_sha256"], root)
    request = json.loads((root / "Request.json").read_bytes())
    require(predict(request, job["generated"]["edit_distance_m"]) == job["generated"]["prediction"], "generated prediction differs from its neutral request")
    for role, directory in (("control", "Controls"), ("generated", "FrozenGenerated")):
        entry = job[role]
        require(Path(entry["filename"]).name == entry["filename"] and entry["filename"].endswith(".SLDPRT"), "invalid plane input basename")
        require(checked(root / directory / entry["filename"], entry["sha256"], root).stat().st_size == entry["bytes"], "frozen plane input length differs")
    return job


def snapshot(author, prediction, edited):
    import Swapp
    from AuthorAssemblySources import feature_tree
    from ReferencePlaneDimensions import circle_geometry, dimension, feature

    wanted = prediction["geometry"]["edited" if edited else "initial"]
    profile = feature(author, prediction["sketch"])
    plane = feature(author, prediction["plane"])
    author.sketch = author.get(profile, "GetSpecificFeature2")
    require(author.sketch is not None, "plane-supported profile has no native sketch")
    origin = author.world_point([0.0, 0.0, 0.0])
    end = author.world_point([0.0, 0.0, 1.0])
    normal = [b - a for a, b in zip(origin, end, strict=True)]
    for index in range(3):
        author.rec.close_number("independent offset sketch origin", origin[index], wanted["plane_origin"][index])
        author.rec.close_number("independent offset sketch normal", normal[index], wanted["normal"][index])
    configuration = author.get(author.model, "GetActiveConfiguration")
    require(str(author.get(configuration, "Name")) == prediction["configuration"], "active part configuration differs")
    extension = author.get(author.model, "Extension")
    require(int(author.get(extension, "GetWhatsWrongCount")) == int(author.get(extension, "NeedsRebuild2")) == 0,
            "native plane graph contains rebuild errors or warnings")
    bodies = list(author.get(author.typed(author.model, "PartDoc"), "GetBodies2", 0, True) or ())
    require(len(bodies) == wanted["body_count"], "plane-supported cylinder body count differs")
    mass = author.rec.call("independent offset cylinder mass", Swapp.mass, author.model)
    actual, expected = [mass["volume"], mass["area"], *mass["com"]], [wanted["volume"], wanted["area"], *wanted["com"]]
    require(all(math.isclose(value, target, rel_tol=5e-7, abs_tol=1e-12) for value, target in zip(actual, expected, strict=True)),
            "plane-supported cylinder differs from the analytical prediction")
    definition = author.declared_interface(author.get(plane, "GetDefinition"), "IRefPlaneFeatureData")
    require(author.get(definition, "AccessSelections", author.model, author.sw.nothing()), "plane selection access failed")
    try:
        constraint = int(author.indexed(definition, "Constraint", 0))
        reference = author.indexed(definition, "Reference", 0)
        distance = float(author.indexed(definition, "AngleOrDistance", 0))
        types = {key: int(author.get(definition, key)) for key in ("Type", "Type2")}
    finally:
        author.get(definition, "ReleaseSelectionAccess")
    require(constraint & 0xFF == 8 and bool(constraint & 256) is prediction["reverse"] and reference is not None,
            "native offset constraint or reverse direction differs")
    author.rec.close_number("native plane-definition distance", distance, wanted["distance_m"])
    parents = [{"name": str(author.get(value, "Name")), "type": str(author.get(value, "GetTypeName2"))} for value in author.get(plane, "GetParents") or ()]
    require({"name": prediction["base_name"], "type": "RefPlane"} in parents, "offset plane lost its selected principal parent")
    plane_parameter, plane_binding = dimension(author, prediction["plane"], "distance", wanted["distance_m"])
    radius_parameter, radius_binding = dimension(author, prediction["sketch"], "radius", wanted["radius_m"], "curve-0")
    depth_parameter = author.get(author.model, "Parameter", "D1@" + prediction["boss"])
    require(depth_parameter is not None, "boss depth parameter is missing")
    author.rec.close_number("native boss depth", author.get(depth_parameter, "SystemValue"), wanted["depth_m"])
    tree = feature_tree(author, author.model)
    names = {row["name"]: row for row in tree}
    semantic = [(name, "RefPlane") for name in prediction["principal_names"].values()]
    semantic += [(prediction["origin"], "OriginProfileFeature"), (prediction["plane"], "RefPlane"),
                 (prediction["sketch"], "ProfileFeature"), (prediction["boss"], "Extrusion")]
    require(all(name in names and names[name]["type"] == kind for name, kind in semantic)
            and all(row["error"] == 0 and row["warning"] is False and row["suppressed"] is False for row in tree),
            "native feature tree differs or contains a failed feature")
    indices = [next(index for index, row in enumerate(tree) if row["name"] == name) for name in (prediction["plane"], prediction["sketch"], prediction["boss"])]
    require(indices == sorted(indices), "the authored plane/profile/boss dependency order changed")
    native_plane = author.declared_interface(author.get(plane, "GetSpecificFeature2"), "IRefPlane")
    transform = author.get(native_plane, "Transform")
    return {"body_count": len(bodies), "mass_properties": mass, "expected_geometry": wanted, "feature_tree": tree,
            "plane": {"constraint": constraint, "type": types["Type"], "type2": types["Type2"], "parents": parents,
                      "distance_m": distance, "transform": [float(value) for value in author.get(transform, "ArrayData")]},
            "sketch_world_origin": origin, "sketch_world_normal": normal,
            "driving_dimensions_m": {"plane_distance": float(author.get(plane_parameter, "SystemValue")),
                                     "radius": float(author.get(radius_parameter, "SystemValue")),
                                     "boss_depth": float(author.get(depth_parameter, "SystemValue"))},
            "dimension_bindings": {"plane": plane_binding, "radius": radius_binding},
            "circle_geometry": circle_geometry(author, profile, wanted["radius_m"])}


def measure(job, root, role, entry, input_path, edited=False):
    import Swapp
    from AuthorReferencePlaneSources import PlaneAuthor, metadata
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity
    from ReferencePlaneDimensions import dimension

    output = root / "Inspection" / role
    output.mkdir(parents=True, exist_ok=False)
    recorder = Recorder(output / "Record.json", {"role": role, "input_sha256": entry["sha256"], "prediction": entry["prediction"]})
    result, controller = {"passed": False}, None
    with AssemblyLoadMonitor() as monitor:
        try:
            api = metadata()
            require(api == json.loads((root / "ApiMetadata.json").read_bytes()), "registered plane interfaces changed")
            recorder.call("verify idle exact oracle", Swapp.sweep)
            controller = recorder.call("launch one fresh plane oracle", Swapp.Sw)
            identity = recorder.call("verify plane oracle identity", application_identity, controller.app)
            result["oracle_identity"] = identity
            require(identity["sha256"] == ORACLE and identity["version_matches"] and controller.revision == "34.5.2", "unexpected plane oracle build")
            author = PlaneAuthor(controller.app, recorder, Swapp, api)
            model, errors, warnings = recorder.call("open exact plane input", controller.open, input_path, read_only=role != "Generated")
            result.update(open_errors=errors, open_warnings=warnings)
            require(model is not None and errors == warnings == 0 and Path(author.get(model, "GetPathName")).samefile(input_path),
                    "native plane open failed, warned or resolved another path")
            author.model = model
            result["initial_body_count"] = len(list(author.get(author.typed(model, "PartDoc"), "GetBodies2", 0, True) or ()))
            result["initial_needs_rebuild"] = int(author.get(author.get(model, "Extension"), "NeedsRebuild2"))
            if result["initial_body_count"]:
                result["initial_mass_properties"] = recorder.call("measure initial native plane body", Swapp.mass, model)
            require(author.get(model, "ForceRebuild3", False), "native plane rebuild failed")
            result["rebuilt"] = snapshot(author, entry["prediction"], edited)
            if role == "Generated":
                parameter, binding = dimension(author, entry["prediction"]["plane"], "distance")
                status = int(author.get(parameter, "SetSystemValue3", entry["edit_distance_m"], 1, author.sw.nothing()))
                require(status == 0 and author.get(model, "ForceRebuild3", False), "generated plane distance edit or rebuild failed")
                result["edit_status"] = status
                result["edited"] = snapshot(author, entry["prediction"], True)
                require(result["rebuilt"]["mass_properties"]["com"] != result["edited"]["mass_properties"]["com"], "plane distance edit did not move the supported solid")
                target = root / "Saved" / (Path(entry["filename"]).stem + "Edited.SLDPRT")
                target.parent.mkdir(exist_ok=False)
                status = list(recorder.call("save edited generated plane sibling", controller.save_as, model, target))
                require(status == [True, 0, 0] and target.is_file(), "edited plane native save failed or warned")
                result["saved"] = {"filename": target.name, "status": status, "sha256": digest(target), "bytes": target.stat().st_size}
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["error"] = repr(error)
        finally:
            if controller is not None:
                try:
                    controller.close()
                    result["controller_diagnostics"] = controller.diagnostics
                except Exception as error:
                    recorder.failure(error, cleanup=True)
    result.update(dialogs=monitor.log, progress_windows=monitor.progress)
    result["passed"] = bool(result["passed"] and not result["dialogs"] and not result.get("controller_diagnostics") and not recorder.data["cleanup_errors"])
    recorder.data.update(result=result, passed=result["passed"], finished_at=time.time())
    recorder.flush()
    return result


def run(path, sha):
    require(os.name == "nt", "native plane measurement runs only in the root-owned Windows guest")
    root, job = path.parent, verify(path, sha)
    inspection = root / "Inspection"
    inspection.mkdir(exist_ok=False)
    inputs = [root / "Controls" / job["control"]["filename"], root / "FrozenGenerated" / job["generated"]["filename"],
              root / "GeneratedInput" / job["generated"]["filename"]]
    immutable = {item: digest(item) for item in inputs}
    require(immutable[inputs[1]] == immutable[inputs[2]] == job["generated"]["sha256"], "actual generated input differs from its frozen sibling")
    result = {"schema": SCHEMA, "packet_sha256": sha, "passed": False, "phases": [], "started_at": time.time()}
    record = inspection / "ReferencePlaneResults.json"

    def phase(role, entry, source, edited=False):
        row = {"role": role, "passed": False}
        result["phases"].append(row)
        write_json(record, result)
        row.update(measure(job, root, role, entry, source, edited))
        write_json(record, result)
        return row

    try:
        if phase("ControlBefore", job["control"], inputs[0])["passed"]:
            generated = phase("Generated", job["generated"], inputs[2])
            if generated["passed"]:
                saved = generated["saved"]
                target = checked(root / "Saved" / saved["filename"], saved["sha256"], root / "Saved")
                reopened = phase("Reopen", job["generated"] | {"sha256": saved["sha256"]}, target, True)
                require(reopened["passed"] and reopened["rebuilt"]["feature_tree"] == generated["edited"]["feature_tree"], "edited generated plane tree changed on fresh reopen")
                require(digest(target) == saved["sha256"], "fresh reopen changed the saved sibling")
    except Exception as error:
        result["exception"] = repr(error)
    finally:
        try:
            phase("ControlAfter", job["control"], inputs[0])
        except Exception as error:
            result["control_after_exception"] = repr(error)
        result["controls_healthy"] = [row["passed"] for row in result["phases"] if row["role"].startswith("Control")] == [True, True]
        result["immutable_inputs_unchanged"] = all(item.is_file() and digest(item) == expected for item, expected in immutable.items())
        identities = {row.get("oracle_identity", {}).get("process_creation_filetime") for row in result["phases"]}
        result["distinct_processes"] = sum(type(value) is int and value > 0 for value in identities)
        result["passed"] = bool(len(result["phases"]) == result["distinct_processes"] == 4 and all(row["passed"] for row in result["phases"])
                                and result["controls_healthy"] and result["immutable_inputs_unchanged"] and not result.get("exception"))
        result["finished_at"] = time.time()
        write_json(record, result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    path = args.packet.resolve(strict=True)
    if args.mode == "verify":
        verify(path, args.packet_sha256)
        print(json.dumps({"verified_packet_sha256": args.packet_sha256, "native_processes_started": 0}))
        return 0
    result = run(path, args.packet_sha256)
    print(json.dumps({key: result[key] for key in ("passed", "controls_healthy", "distinct_processes", "immutable_inputs_unchanged")}))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
