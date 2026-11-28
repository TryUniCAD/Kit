from argparse import ArgumentParser
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from subprocess import check_output, run
from tarfile import open as open_tar
from tempfile import TemporaryDirectory
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from BoxTopology import COUNTS, portable_roles, require, source_roles
from NativeLineage import expected_primary, part_owners, saved_kernel


REVISION = "a1b26105b401a75edd32930847a96da45394a811"
INPUTS = {
    "SdkFreecadBoxReleaseNative01": "e87ae3d9520edcffd262b1dc2457b2bd4e5a70fe4ff34c1a1271079d5628b856",
    "SdkFreecadF14aIntactSource01": "89820d391925543775ea2ba05e56197ee0827a7ece06cd2451347985f540f9a4",
}
HELPER = "re/tooling/sw2026/VerifyFreecadF14aIntact.py"
HELPER_SHA256 = "9f73969bd176cc19ea10d942de0f334d303b3342b90b7fbbc6d5079d83514f20"
PARTITION_TOOLS = ("para/Partition.py", "para/Schema.py", "builders/EmptyPartition.py")
PROFILES = {"Freecad102": "1.0.2", "Freecad114": "1.1.4"}
HEIGHT_DRIVER = "Height@AdditiveBox"


def checked(path, expected):
    require(path.is_file() and not path.is_symlink(), "expected an exact disclosed evidence file")
    data = path.read_bytes()
    require(sha256(data).hexdigest() == expected, "evidence SHA-256 changed")
    return data


def source_lineage(path, evidence):
    from convert import open_document
    from VerifyFreecadF14aIntact import source_archive

    raw = checked(path, evidence["original_sha256"])
    document = open_document(path, strict=True, include_brep=True, include_tessellation=True)
    document.assert_valid()
    entries, owners = source_archive(raw, document)
    require(owners == evidence["physical"], "physical FreeCAD owner table differs from the established source audit")
    feature, = document.feature_timeline
    body, = document.bodies
    solid, = document.brep.bodies
    require(solid.attributes["brep_payload_id"] == "freecad:brep:Body:Shape"
            and solid.design_body_id == body.id and solid.attributes["feature_id"] == body.final_feature_id == feature.id,
            "source Shape is no longer bound to the actual PartDesign producer")
    driver_order = tuple(next(row.value.value for row in document.parameters if row.attributes["freecad_path"] == name)
                         for name in ("Length", "Width", "Height"))
    payloads = {row.id: row for row in document.brep_payloads}
    body_shape, primitive_shape = (payloads[f"freecad:brep:{owner}:Shape"] for owner in ("Body", "AdditiveBox"))
    require(body_shape.data == entries["Body.Shape.brp"] and primitive_shape.data == entries["AdditiveBox.Shape.brp"]
            and primitive_shape.attributes["feature_id"] == feature.id, "strict source neutral payloads lack their literal owners")
    reported = evidence["retained_owners"]["payloads"]
    for shape in (body_shape, primitive_shape):
        require(sha256(shape.data).hexdigest() == shape.sha256 == reported[shape.id]["sha256"], "source Shape identity differs")
    source_portable = portable_roles(document.brep, driver_order)
    prefix = solid.id.rsplit(":body:", 1)[0]
    body_order = source_roles(body_shape.data, prefix, body.id, driver_order)
    primitive_order = source_roles(primitive_shape.data, "freecad:primitive:shape", body.id, driver_order)
    for kind in COUNTS:
        binding = owners["body_element_map"][kind]
        require(binding["child_xml_object_id"] == owners["object_ids"]["AdditiveBox"]
                and binding["child_start_index"] == 1 and binding["index_offset"] == 0
                and binding["member_count"] == COUNTS[kind] and binding["child_map_index"] == binding["string_id_count"] == 0
                and binding["child_count"] == 1 and binding["local_name_count"] == 0,
                "source model has an unqualified child map")
        require(source_portable[kind].keys() == body_order[kind].keys() == primitive_order[kind].keys(),
                "source body, its Shape and actual producer do not share the same boundary roles")
        for role, row in body_order[kind].items():
            require(row["neutral_entity_id"] == source_portable[kind][role]["entity_id"]
                    and row["ordinal"] == primitive_order[kind][role]["ordinal"],
                    "literal FreeCAD indexed child refers to another geometric entity")
    return {"source_uuid": owners["source_uuid"], "body_xml_id": owners["object_ids"]["Body"],
            "primitive_xml_id": owners["object_ids"]["AdditiveBox"], "original_sha256": evidence["original_sha256"],
            "body_shape_sha256": body_shape.sha256, "primitive_shape_sha256": primitive_shape.sha256,
            "source_element_map_sha256": sha256(entries["Body.Shape.Map.txt"]).hexdigest(),
            "body_entities": body_order, "primitive_entities": primitive_order}, driver_order


def inspect_lifecycle(packet, native, oracle, generated_hash, saved_hash):
    role = native["role"]
    cases = {}
    for phase, expected_hash, pin in zip(("Generated", "FreshReopen"), (generated_hash, saved_hash), native["native_record_sha256"], strict=True):
        data = json.loads(checked(packet / "Inspection" / role / phase / "Record.json", pin))
        result = data["result"]
        identity = result["oracle_identity"]
        methods = {row["method"] for row in data["api_calls"]}
        observe_tokens = any(marker in method for marker in ("PersistReference", "PersistentID") for method in methods)
        require(data["job"] == {"role": phase, "input_sha256": expected_hash}
                and result["passed"] and result["immutable_input"] and result["open_errors"] == result["open_warnings"] == 0
                and identity["version_matches"] and identity["sha256"] == oracle and not observe_tokens,
                "prior native phase does not establish the scoped clean identity boundary")
        require(all(state["body_topology"] == [8, 12, 6] and state["body_count"] == 1 for state in result["states"].values()),
                "prior native lifecycle has alternate solid topology")
        cases[phase] = result
    initial, reopened = (cases[key] for key in ("Generated", "FreshReopen"))
    require(initial["saved_sha256"] == saved_hash and initial["save_status"] == [True, 0, 0]
            and initial["signature"] == reopened["signature"] and initial["roles"] == reopened["roles"]
            and len(initial["states"]) == 7 and len(reopened["states"]) == 2,
            "native edit/save/reopen custody or parametric signature changed")
    edited_mm = tuple(initial["saved_dimensions_m"][name] * 1000.0 for name in
                      ("Length@AdditiveBox Profile", "Width@AdditiveBox Profile", HEIGHT_DRIVER))
    return edited_mm, {"original_native_phase_hashes": native["native_record_sha256"],
                       "exact_native_save_is_the_fresh_reopen_input": True, "native_persistent_api_calls": 0,
                       "prior_state_counts": [len(initial["states"]), len(reopened["states"])],
                       "observed_edited_dimensions_mm": edited_mm}


def measure(sdk, request):
    sys.path[:0] = [str(sdk / "src"), str(sdk / "rules"), str(Path(__file__).resolve().parent.parent)]
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Container.Format import KLocalBodyStream, KPartitionStream

    role, release = request["native"]["role"], request["native"]["source_release"]
    require(PROFILES[role] == release, "native role has another disclosed source release")
    packet = Path(request["packet"])
    native, source = request["native"], request["source"]
    mapped, original_sizes = source_lineage(Path(request["original"]), source)
    generated_sha, saved_sha = native["generated"]["file_sha256"], native["saved_and_reopened"]["file_sha256"]
    require(generated_sha == source["generated_projection"]["generated_sha256"]
            and mapped["original_sha256"] == native["source_freecad_sha256"], "native lineage has a different prior source binding")
    edited_mm, lifecycle = inspect_lifecycle(packet, native, request["oracle"], generated_sha, saved_sha)
    require(edited_mm[:2] == original_sizes[:2] and edited_mm[2] != original_sizes[2], "saved model does not isolate the final Height edit")
    raw_generated = checked(packet / "Inputs" / role / "F14a.SLDPRT", generated_sha)
    raw_saved = checked(packet / "Inspection" / role / "Generated" / "Edited.SLDPRT", saved_sha)
    cold = SldprtArchive.from_bytes(raw_generated)
    saved = SldprtArchive.from_bytes(raw_saved)
    start, edited = (open_document(raw, source_format="solidworks.sldprt", strict=True) for raw in (raw_generated, raw_saved))
    start.assert_valid()
    edited.assert_valid()
    require(not ({KPartitionStream, KLocalBodyStream} & cold.streams.keys()) and not start.brep_payloads,
            "generated original unexpectedly carries a native body cache")
    cold_owners = part_owners(cold, start, original_sizes)
    saved_owners = part_owners(saved, edited, edited_mm)
    require(cold_owners["boss_mark"] is cold_owners["configuration_mark"] is None
            and all(cold_owners[key] == saved_owners[key] for key in
                    ("boss_id", "profile_id", "side_markers", "has_producer_creation_event", "feature_reference_time", "body_atom_id")),
            "archive producer, reference time, or side marker changed across the edit")
    cold_roles, saved_roles = portable_roles(start.brep, original_sizes), portable_roles(edited.brep, edited_mm)
    kernel = saved_kernel(saved, edited, saved_roles, saved_owners, cold_owners, edited_mm)
    rows = []
    for kind in COUNTS:
        require(mapped["body_entities"][kind].keys() == cold_roles[kind].keys() == saved_roles[kind].keys(),
                "source, generated and native-saved entity sets do not join one to one")
        for role in sorted(cold_roles[kind]):
            before, after = cold_roles[kind][role], saved_roles[kind][role]
            require(before["corner_roles"] == after["corner_roles"] and before["touching_faces"] == after["touching_faces"],
                    "height edit changes portable topology incidence")
            record = {"kind": kind, "role": role, "actual_incident_faces": after["touching_faces"],
                      "source_body": mapped["body_entities"][kind][role], "source_primitive": mapped["primitive_entities"][kind][role],
                      "generated_sdk_entity_id": before["entity_id"], "actual_saved_wire": kernel["entities"][kind][role]}
            if kind != "face":
                record["derived_incident_face_keys"] = [expected_primary(face, cold_owners) for face in after["touching_faces"]]
            rows.append(record)
    del mapped["body_entities"], mapped["primitive_entities"], kernel["entities"]
    return {"source": mapped, "generated_sha256": generated_sha, "saved_sha256": saved_sha,
            "generated_native_boundary_identities_present": False, "portable_entity_counts": COUNTS,
            "part_before_edit": cold_owners, "part_after_edit": saved_owners, "native_lifecycle": lifecycle,
            "saved_kernel": kernel, "entity_rows": rows,
            "persistent_reference_admission": "refused_missing_baseline_and_live_persistent_resolution"}


def main(packet, fixtures):
    root = Path(__file__).resolve().parents[4]
    inputs = {name: json.loads(checked(root / f"re/solidworks/measurements/2026/{name}.json", wanted)) for name, wanted in INPUTS.items()}
    native = inputs["SdkFreecadBoxReleaseNative01"]
    intact = inputs["SdkFreecadF14aIntactSource01"]
    require(native["oracle_build"] == "34.5.2.0604" and native["scoped_native_lifecycle_passed"]
            and native["native_processes"] == 6 and not native["heldout_inputs_read"]
            and intact["sdk_revision"] == REVISION and not intact["public_writer_qualified"], "earlier provenance is outside the disclosed scope")
    for phase, expected in native["healthy_control_records_sha256"].items():
        require(phase in {"ControlBefore", "ControlAfter"}, "prior native control has a foreign role")
        row = json.loads(checked(packet / "Inspection" / phase / "Record.json", expected))
        require(row["opened"] and row["rebuilt"] and row["bodies"] > 0 and not row["dialogs"]
                and row["open_errors"] == row["open_warnings"] == row["whats_wrong"] == 0
                and row["oracle_identity"]["sha256"] == native["oracle_executable_sha256"], "prior native control differs")
    source_helpers = {HELPER: sha256(checked(root / HELPER, HELPER_SHA256)).hexdigest()}
    report = {}
    with TemporaryDirectory(prefix="kit-f14a-lineage-") as isolated:
        sdk = Path(isolated)
        raw = check_output(("git", "-C", str(root), "archive", "--format=tar", REVISION, "src"))
        with open_tar(fileobj=BytesIO(raw)) as archive:
            archive.extractall(sdk, filter="data")
        for tool in PARTITION_TOOLS:
            known_path = f"re/tooling/sw2026/{tool}"
            code = check_output(("git", "-C", str(root), "show", f"{REVISION}:{known_path}"))
            path = sdk / "rules" / tool
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(code)
            source_helpers[known_path] = sha256(code).hexdigest()
        for native_row in native["cases"]:
            role = native_row["role"]
            case = f"recipe-{PROFILES[role]}-F14a"
            request = {"packet": str(packet), "original": str(fixtures / f"{case}.FCStd"), "native": native_row,
                       "source": intact["cases"][case], "oracle": native["oracle_executable_sha256"]}
            captures = []
            for _ in range(2):
                result = run((sys.executable, "-I", "-B", __file__, "--worker", isolated), input=json.dumps(request),
                             text=True, capture_output=True, cwd=sdk, timeout=120)
                require(result.returncode == 0 and not result.stderr, result.stderr)
                captures.append(json.loads(result.stdout))
            require(captures[0] == captures[1], "independent native identity comparisons differ")
            report[role] = captures[0]
    require(set(report) == set(PROFILES), "report lost an exact disclosed source case")
    return {"schema": "kit.sw2026.freecad-f14a-topology-lineage.v1", "sdk_revision": REVISION, "oracle_build_from_prior_receipt": native["oracle_build"],
            "prior_receipts_sha256": INPUTS, "tool_dependencies_sha256": source_helpers, "cases": report,
            "independent_processes": 4, "native_processes_started": 0, "protected_inputs_read": 0,
            "writer_outputs": 0, "public_writer_qualified": False, "native_reference_persistence_qualified": False}


if __name__ == "__main__":
    if sys.argv[1:2] == ["--worker"]:
        result = measure(Path(sys.argv[2]), json.load(sys.stdin))
    else:
        parser = ArgumentParser(description="Check the exact disclosed F14a body topology and stored creator identities")
        parser.add_argument("native_packet", type=Path)
        parser.add_argument("disclosed_fixtures", type=Path)
        options = parser.parse_args()
        result = main(options.native_packet.resolve(strict=True), options.disclosed_fixtures.resolve(strict=True))
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
