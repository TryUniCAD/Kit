from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import sys


SCHEMA = "kit.sw2026.generated-offset-plane-readback.v1"
NATIVE_SCHEMA = "kit.sw2026.generated-offset-plane-native-trial.v1"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
SOURCE_LOCK = "c61560deff9c84addd65db48664ce6a5488ad3eecde9a070c62a215a5541d703"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def frozen(path, expected):
    require(path.is_absolute() and path.resolve(strict=True) == path and not path.is_symlink()
            and re.fullmatch(r"[0-9a-f]{64}", expected) and digest(path) == expected,
            "the declared audit input changed or escaped its canonical path")
    return json.loads(path.read_bytes())


class NativeReads:
    def __init__(self, root, paths):
        self.root = root
        self.allowed = set(paths)
        self.native = {path for path in paths if path.suffix.casefold() == ".sldprt"}
        self.events = []
        self.denied = 0

    def observe(self, event, arguments):
        if event != "open" or not isinstance(arguments[0], (str, bytes)):
            return
        path = Path(arguments[0].decode() if isinstance(arguments[0], bytes) else arguments[0]).resolve()
        mode, flags = arguments[1:3]
        native = path.suffix.casefold() in (".sldprt", ".sldasm", ".slddrw", ".fcstd")
        protected = path.is_relative_to(self.root)
        writing = isinstance(mode, str) and any(letter in mode for letter in "wax+") or bool(flags & 3)
        if native and path not in self.native or protected and (writing or path not in self.allowed):
            self.denied += 1
            raise PermissionError("generated readback blocked another CAD artifact or a frozen-packet mutation")
        if native:
            self.events.append(path.relative_to(self.root).as_posix())

    def report(self):
        return {"allowed_native_files": len(self.native), "native_open_events": len(self.events),
                "distinct_native_files_opened": sorted(set(self.events)), "denied_events": self.denied,
                "heldout_inputs_read": 0, "packet_write_events": 0}


def load_code(root, manifest_path, expected):
    require(root.is_absolute() and root.resolve(strict=True) == root, "the frozen code root is not canonical")
    manifest = frozen(manifest_path, expected)
    for name, identity in manifest["files_sha256"].items():
        relative = Path(name)
        require(not relative.is_absolute() and ".." not in relative.parts and relative.suffix == ".py",
                "the frozen code manifest contains another input kind")
        path = root / relative
        require(path.resolve(strict=True) == path and not path.is_symlink() and digest(path) == identity,
                "the frozen serializer code closure changed")
    for directory in (root / "src", root / "re/tooling/sw2026", root / "re/tooling/sw2026/serial"):
        sys.path.insert(0, str(directory))
    import AuditReferencePlaneSources as sources
    return sources, manifest


def tree_changes(before, after):
    return [{"index": index, "before": left, "after": right}
            for index, (left, right) in enumerate(zip(before, after, strict=True)) if left != right]


def project(path, identity, prediction, edited, snapshot, sources):
    from Core import Obj
    from ReferencePlaneCompatibilityRead import project_face_offset
    from ReferencePlaneReadRules import near

    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == identity["sha256"] and len(raw) == identity["bytes"],
            "the native sibling changed before typed readback")
    archive = sources.SldprtArchive.from_bytes(raw, path)
    require(archive.format_version == 4 and sources.ContainerMo(archive.streams) == 19000,
            "the readback requires container 4 and model version 19000")
    rules = sources.registry()
    streams = sources.stream_reports(archive, rules)
    require(all(row["passed"] for row in streams.values()), "a scoped native stream failed exact typed round-trip")
    configuration, config_map = sources.load_config(archive.require(sources.CONFIG), rules, 19000, archive=archive, name=sources.CONFIG)
    resolved, resolved_map = sources.load_resolved(archive.require(sources.RESOLVED), rules, 19000,
                                                 archive=archive, name=sources.RESOLVED, seed=config_map.map_state())
    require(not configuration.tail and not resolved.tail and resolved_map.base == config_map.count,
            "the native sibling lost its linked Config/Resolved archive context")
    stored, seed = sources.store_config_state(configuration, rules, 19000)
    require(stored == archive.require(sources.CONFIG) and
            sources.store_resolved(resolved, rules, 19000, seed=seed) == archive.require(sources.RESOLVED),
            "the native sibling lost its re-emitted configuration object identity")
    require((prediction["plane"], prediction["sketch"], prediction["boss"]) == ("OffsetPlane", "PlaneSketch", "PlaneBoss"),
            "this initial auditor uses the disclosed ordinary plane/profile/boss naming profile")
    model, = configuration.roots
    expected = prediction["geometry"]["edited" if edited else "initial"]
    case = {"base": {"x": "right", "y": "top", "z": "front"}[prediction["base_axis"]], "reverse": prediction["reverse"]}
    plane = project_face_offset(model, resolved.roots, resolved_map, case, expected, snapshot)
    plane_node, = [node for node in resolved.roots if node.cls == "moRefPlane_c" and node["f18"]["f08"] == prediction["plane"]]
    display_value = plane_node["f6f8"]["f98"]["fad0"]
    expected_display = expected["distance_m"] if edited else 0.0
    profile, = [node for node in resolved.roots if node.cls == "moProfileFeature_c" and node["f18"]["f08"] == prediction["sketch"]]
    radial, = [row["o"] for row in profile["pd_f80"]["dims"]["f118"]["items"] if row["o"].cls == "moDisplayRadialDim_c"]
    radial_handle, = [row["o"] for row in radial["f850"]]
    require(radial_handle.cls == "moSkDimHandleRadial_c" and radial_handle["ff0"] is profile["pd_f80"],
            "the radial display lost its actual sketch dimension handle")
    values = profile["pd_f80"]["dims"]["val_g1"]
    require(0 <= radial_handle["ff8"] < len(values), "the radial handle leaves its owning value-dimension array")
    radius_dimension = values[radial_handle["ff8"]]["d"]
    require(radius_dimension.cls == "sgCircleDim", "the radial handle selects another dimension family")
    radius = radius_dimension["f28"]
    materials = {id(entry[1]): entry[1] for entry in resolved_map.table.values()
                 if entry[0] == "obj" and isinstance(entry[1], Obj) and entry[1].cls == "moMaterialFolder_c"}
    material, = materials.values()
    manager = sources.read_root(archive, rules, "Contents/CMgr", "moConfigurationMgr_c")
    header = sources.read_root(archive, rules, "Header2", "moHeader_c")
    manager_header = sources.read_root(archive, rules, "Contents/CMgrHdr2", "dmConfigMgrHeader_c")
    config_header, = [row["o"] for row in manager_header["f08"]["items"]]
    active = manager["f360"]
    model_header = configuration.head["model_header"]
    checks = {"plane_inputs_match_neutral_and_native": all(value for key, value in plane["checks"].items()
                                                         if key != "display_value_matches_parameter"),
              "distance_display_cache_matches_lifecycle": near([display_value], [expected_display]),
              "radius_parameter_matches_neutral": near([radius["f58"]], [expected["radius_m"]]),
              "radius_cache_matches_parameter": near([radial["f950"]], [radius["f58"]]),
              "radial_reference_norm_matches_offset": near([radial["fad0"]], [expected["distance_m"]]),
              "material_is_unassigned": material["f378"] == "" and material["flags380"] == 0x80000000,
              "model_and_top_update_stamps_agree": model_header["f40"] == header["f40"],
              "configuration_update_matches_header": active["f860"] == config_header["f38"],
              "configuration_name_matches_request": active["f18"]["f08"] == config_header["f10"] == prediction["configuration"]}
    require(path.read_bytes() == raw, "the typed readback changed an immutable sibling")
    return {"sha256": identity["sha256"], "bytes": len(raw), "stream_inventory": sorted(archive.streams),
            "streams": streams, "projection": plane,
            "distance_display_cache": {"value_m": display_value, "expected_m": expected_display,
                                       "lifecycle": "native_edited_save" if edited else "fresh_shared_constructor",
                                       "fresh_rule": "shared common_display_fields initializes fad0 to zero",
                                       "native_saved_profile_cache_check_passed": plane["checks"]["display_value_matches_parameter"]},
            "radius": {"value_m": radius["f58"], "parameter_name": radius["f18"]["f08"],
                       "parameter_id": radius["f08"], "cache_m": radial["f950"], "reference_norm_m": radial["fad0"]},
            "material": {"name": material["f18"]["f08"], "material_string": material["f378"], "flags380": material["flags380"]},
            "headers": {"model_update": model_header["f40"], "top_update": header["f40"],
                        "configuration_update": active["f860"], "configuration_header_update": config_header["f38"],
                        "manager_save_time": manager_header["f60"],
                        "configuration_header": {key: config_header[key] for key in ("f08", "f10", "f30", "f38", "f34", "f40", "f44", "f48", "f50", "f4c")}},
            "map": {"config_base": config_map.base, "config_count": config_map.count,
                    "resolved_base": resolved_map.base, "resolved_count": resolved_map.count, "re_emitted_seed_continuity": True},
            "checks": checks, "passed": all(checks.values())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--native-sha256", required=True)
    parser.add_argument("--code-root", type=Path, required=True)
    parser.add_argument("--code-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.packet.parent.resolve(strict=True)
    require(args.packet.parent == root and args.packet.name == "Trial.json", "use a canonical generated trial packet")
    job = frozen(args.packet, args.packet_sha256)
    require(job["schema"] == NATIVE_SCHEMA and job["source_lock_sha256"] == SOURCE_LOCK and job["oracle_sha256"] == ORACLE
            and job["heldout_inputs_tested"] == 0 and job["native_acceptance"] is False, "another native discovery profile was supplied")
    native_path = root / "Inspection/ReferencePlaneResults.json"
    native = frozen(native_path, args.native_sha256)
    require(native["schema"] == NATIVE_SCHEMA and native["packet_sha256"] == args.packet_sha256
            and native["controls_healthy"] and native["immutable_inputs_unchanged"] and native["distinct_processes"] == 4,
            "the native subphase evidence lacks healthy controls, immutable inputs or four identities")
    require([row["role"] for row in native["phases"]] == ["ControlBefore", "Generated", "Reopen", "ControlAfter"]
            and all(row["passed"] and row["open_errors"] == row["open_warnings"] == 0 and row["oracle_identity"]["sha256"] == ORACLE
                    for row in native["phases"]), "a native phase failed its independent snapshot")
    generated, reopened = native["phases"][1:3]
    require(generated["saved"]["status"] == [True, 0, 0], "the native edited sibling did not save cleanly")
    source_path = root / "FrozenGenerated" / job["generated"]["filename"]
    saved_path = root / "Saved" / generated["saved"]["filename"]
    require(source_path.resolve(strict=True) == source_path and saved_path.resolve(strict=True) == saved_path,
            "a native sibling escaped the declared generated packet")
    custody = NativeReads(root, (args.packet, native_path, source_path, saved_path, root / "CodeManifest.json"))
    sys.addaudithook(custody.observe)
    sources, manifest = load_code(args.code_root, args.code_manifest, job["code_manifest_sha256"])
    require(all(manifest["files_sha256"].get(name) == identity for name, identity in job["writer_files_sha256"].items()),
            "the audit serializer closure differs from the native writer identity")
    prediction = job["generated"]["prediction"]
    siblings = {"generated": project(source_path, job["generated"], prediction, False, generated["rebuilt"], sources),
                "edited_saved": project(saved_path, generated["saved"], prediction, True, reopened["rebuilt"], sources)}
    before, after = [siblings[key]["projection"] for key in ("generated", "edited_saved")]
    edits = {"plane_identity_preserved": before["plane_feature_id"] == after["plane_feature_id"],
             "dimension_identity_preserved": before["distance_graph"]["dimension_persistent_id"] == after["distance_graph"]["dimension_persistent_id"],
             "support_identity_preserved": before["support_feature_id"] == after["support_feature_id"],
             "distance_persists_declared_edit": before["distance_m"] == prediction["geometry"]["initial"]["distance_m"]
                 and after["distance_m"] == prediction["geometry"]["edited"]["distance_m"],
             "boss_depth_preserved": before["boss_depth_m"] == after["boss_depth_m"],
             "radius_preserved": siblings["generated"]["radius"]["value_m"] == siblings["edited_saved"]["radius"]["value_m"]}
    result = {"schema": SCHEMA, "packet_sha256": args.packet_sha256, "native_result_sha256": args.native_sha256,
              "native_aggregate_passed": native["passed"], "native_aggregate_exception": native.get("exception"),
              "native_subphases_passed": True, "code_manifest_sha256": job["code_manifest_sha256"],
              "writer_revision": job["writer_revision"], "siblings": siblings, "edit_checks": edits,
              "tree_differences": tree_changes(generated["edited"]["feature_tree"], reopened["rebuilt"]["feature_tree"]),
              "source_read_custody": custody.report(), "code_fingerprints": sources.source_fingerprints(),
              "audit_tool_sha256": digest(Path(__file__)), "native_processes_started": 0, "writer_output_count": 0,
              "heldout_inputs_read": 0, "native_acceptance": False, "full_field_classification_claimed": False,
              "passed": all(row["passed"] for row in siblings.values()) and all(edits.values())}
    require(args.output.is_absolute() and args.output.parent.resolve(strict=True) == args.output.parent
            and not args.output.exists() and not args.output.is_relative_to(root), "use an unused absolute output outside the frozen packet")
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "sha256": digest(args.output),
                      "native_aggregate_passed": native["passed"], "tree_differences": len(result["tree_differences"]),
                      "heldout_inputs_read": 0, "writer_output_count": 0}))
    raise SystemExit(0 if result["passed"] else 3)


if __name__ == "__main__":
    main()
