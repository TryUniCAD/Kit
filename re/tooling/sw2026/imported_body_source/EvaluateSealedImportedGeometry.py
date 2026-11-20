from argparse import ArgumentParser
from codecs import lookup
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
from shutil import copyfile
import sys


ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026"), str(ROOT / "re/tooling/sw2026/serial")]

from AuthorCurves import digest, require, write_json
from AuthorImportedBody import box_expectation
from AuthorRectangleAnchors import CONTROL, ORACLE, control
from BuildImportedLocalPart import AUTHORED_AMBIENT, make_part, verify_part
from ObserveLocalImportedPart import phase
from ProjectDisclosedImport import decode_import, project_import
from interchange import CadDocument
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit


SOURCE_ROOT = Path(r"C:\KitImportedBodySources04")
SEALED_RECEIPT = "1a5a4993881c967682496c90924c262c7954fddd67dd9d1ee3e105186deed281"
SLOTS = ("Slot01", "Slot02")
OPERATORS = (
    "BuildImportedLocalPart.py", "EvaluateSealedImportedGeometry.py", "ProjectDisclosedImport.py",
    "ObserveLocalImportedPart.py", "BuildLocalBodyKernel.py", "LocalBodyKernel.py",
)
SCENE_OPERATORS = ("ProbeImportedPartScene.py", "VerifyBareImportPackage.py", "ProjectImportedSemantics.py")


def expected_shape(specification):
    box = box_expectation(specification)
    return {"corners_m": box["corners"], "edges": len(box["edges"]), "faces": len(box["faces"]),
            "com_m": box["com"], "volume_m3": box["volume"], "area_m2": box["area"]}


def make_guarded(raw, target, audit):
    original = decode_import(raw)
    audit.BeginBuild()
    running = True

    def guard(event, args):
        if running:
            audit.InspectEvent(event, args)
            if event.startswith("socket.") or event == "ctypes.dlopen":
                raise PermissionError(f"sealed imported geometry construction attempted {event}")

    sys.addaudithook(guard)
    try:
        projection = project_import(original)
        recipe = {"kit.sw2026.ambient": asdict(AUTHORED_AMBIENT)}
        model = CadDocument(CadSource("kit.neutral", "", ""),
                            (Configuration("local", projection.configuration_name, True),),
                            (), (), (), (), (), (), brep=projection.model, metadata=recipe)
        blob, streams = make_part(model, str(target), "Owned", completed=True, feature_name=projection.feature_name)
        details = verify_part(blob, streams)
        require(not audit.DeniedReads and details["feature"] == projection.feature_name,
                "generated import lost its projected name or used runtime reads")
    finally:
        running = False
    return blob, projection, details


def evaluate(slot, source_lock, specification, output):
    source = SOURCE_ROOT / slot / "Source.SLDPRT"
    expected_hash = source_lock["source_sha256"]
    require(digest(source) == expected_hash, "sealed native source changed")
    raw = source.read_bytes()
    require(sha256(raw).hexdigest() == expected_hash, "sealed native source changed during intake")
    target = output / (slot + ".SLDPRT")
    saved = output / (slot + "Saved.SLDPRT")
    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    blob, projection, details = make_guarded(raw, target, audit)
    second, repeated, _ = make_guarded(raw, target, audit)
    require(blob == second and projection == repeated, "sealed neutral projection is not deterministic")
    with target.open("xb") as file:
        file.write(blob)
    checksum = sha256(blob).hexdigest()
    expected = expected_shape(specification)
    native = phase(output, slot + "Original", source, expected_hash, expected, projection.feature_name)
    require(native["passed"], "the independently authored original failed native comparison")
    candidate = phase(output, slot + "Candidate", target, checksum, expected, projection.feature_name, save=saved)
    require(candidate["passed"], "the generated held-out part failed its first lifecycle")
    reopened = phase(output, slot + "Reopen", saved, candidate["saved_sha256"], expected, projection.feature_name,
                     reference=candidate["rebuilt"]["persistent_reference"])
    require(reopened["passed"] and digest(source) == expected_hash, "fresh reopen failed or the sealed source changed")
    phases = (native, candidate, reopened)
    return {
        "input_sha256": expected_hash, "candidate_sha256": checksum, "saved_candidate_sha256": candidate["saved_sha256"],
        "model_generated_streams": len(details["streams"]), "runtime_input_file_reads": len(audit.DeniedReads),
        "declared_projection_omissions": projection.omissions,
        "omitted_capabilities": projection.omitted_capabilities,
        "omitted_metadata": projection.omitted_metadata,
        "numeric_candidate_checks": candidate["numeric_checks"] + reopened["numeric_checks"],
        "cold_rebuild_save_reopen": True, "source_unchanged": True,
        "native_phase_records": [row["record_sha256"] for row in phases],
    }, [tuple(row["oracle_identity"][key] for key in ("process_id", "process_creation_filetime")) for row in phases]


def evaluate_scene(slot, source_lock, specification, output, *, preserve_empty_file_owner=False):
    from ProbeImportedPartScene import compare, decoded_scene_row, light_scene, prepared_part, read_checked
    from ProjectImportedSemantics import project_part_text, read_empty_file_owner

    source = SOURCE_ROOT / slot / "Source.SLDPRT"
    source_hash = source_lock["source_sha256"]
    original = read_checked(source, source_hash)
    target = output / (slot + ".SLDPRT")
    saved = output / (slot + "Saved.SLDPRT")
    generated, build = prepared_part(original, target, preserve_empty=True, preserve_empty_file_owner=preserve_empty_file_owner)
    other, repeat = prepared_part(original, target, preserve_empty=True, preserve_empty_file_owner=preserve_empty_file_owner)
    require(generated == other and build == repeat and build["runtime_file_reads"] == 0,
            "sealed semantic build was nondeterministic or read files")
    require(build["explicit_empty_text_owners_preserved"], "selected source text owners are missing")
    with target.open("xb") as file:
        file.write(generated)
    expected = expected_shape(specification)
    scene = build["native_scene"]
    native = phase(output, slot + "Original", source, source_hash, expected, build["feature"], scene=scene)
    require(native["passed"], "independent original geometry and scene did not pass")
    candidate = phase(output, slot + "Candidate", target, build["file"]["sha256"], expected,
                      build["feature"], save=saved, scene=scene)
    require(candidate["passed"], "generated sealed candidate failed open rebuild or save")
    reopened = phase(output, slot + "Reopen", saved, candidate["saved_sha256"], expected,
                     build["feature"], reference=candidate["rebuilt"]["persistent_reference"], scene=scene)
    require(reopened["passed"] and digest(source) == source_hash, "native reopen failed or original changed")
    saved_data = read_checked(saved, candidate["saved_sha256"])
    folder, lights = light_scene(saved_data)
    native_text = project_part_text(decode_import(saved_data), preserve_empty=True)
    source_text = project_part_text(decode_import(original), preserve_empty=True)
    require(decoded_scene_row(folder, lights) == scene and compare(tuple(map(asdict, lights)), build["neutral_lights"])
            and native_text == source_text,
            "a saved source light or empty text scope changed")
    phases = (native, candidate, reopened)
    report = {
        "input_sha256": source_hash, "candidate_sha256": build["file"]["sha256"],
        "saved_candidate_sha256": candidate["saved_sha256"], "model_generated_streams": build["stream_count"],
        "runtime_input_file_reads": 0, "saved_light_values": sum(len(asdict(light)) for light in lights),
        "saved_empty_text_scopes": len(native_text.EmptyScopes), "source_unchanged": True,
        "numeric_candidate_checks": candidate["numeric_checks"] + reopened["numeric_checks"],
        "native_phase_records": [row["record_sha256"] for row in phases],
    }
    if preserve_empty_file_owner:
        original_owner = read_empty_file_owner(original)
        require(read_empty_file_owner(saved_data) == original_owner, "native save changed the empty file owner")
        report["file_property_owner"] = build["file_property_owner"]
    return report, [tuple(row["oracle_identity"][key] for key in ("process_id", "process_creation_filetime")) for row in phases]


def run(job_path, checksum):
    require(os.name == "nt" and digest(job_path) == checksum, "run the frozen evaluator inside the exact guest")
    job = json.loads(job_path.read_bytes())
    schema = job["schema"]
    paths = {
        "kit.sw2026.sealed-import-geometry-job.v1": Path(r"C:\KitImportedEvaluation01"),
        "kit.sw2026.sealed-import-scene-text-job.v1": Path(r"C:\KitImportedEvaluation02"),
        "kit.sw2026.sealed-import-property-owner-job.v1": Path(r"C:\KitImportedEvaluation03"),
    }
    require(job["oracle_sha256"] == ORACLE and schema in paths, "unexpected sealed import evaluator profile")
    output = Path(job["guest_output"])
    require(output == paths[schema] and not output.exists(), "use the owned separate evaluation path")
    property_mode = schema == "kit.sw2026.sealed-import-property-owner-job.v1"
    scene_mode = property_mode or schema == "kit.sw2026.sealed-import-scene-text-job.v1"
    operator_folder = Path(__file__).resolve().parent
    require(set(job["operators"]) == set(OPERATORS + (SCENE_OPERATORS if scene_mode else ())) and
            all(digest(operator_folder / name) == checksum for name, checksum in job["operators"].items()),
            "sealed evaluator code differs from the frozen revision")
    frozen_dir = job_path.parent
    require(digest(frozen_dir / "SealedSourceReceipt.json") == SEALED_RECEIPT, "source cohort receipt hash differs")
    locks = json.loads((frozen_dir / "SealedSourceReceipt.json").read_bytes())
    require(locks["passed"] and locks["controls_healthy"] and locks["heldout_sources_locked"] == len(SLOTS)
            and set(locks["sources"]) == set(SLOTS) and locks["heldout_payloads_shared"] == 0,
            "source cohort is not a sealed, controlled native batch")
    specifications = SOURCE_ROOT / "SourceSpecifications.json"
    require(digest(specifications) == locks["specifications_sha256"], "sealed independent expectations changed")
    external_seed = frozen_dir / "Control.SLDPRT"
    require(digest(external_seed) == CONTROL and not (frozen_dir / "Result.json").exists(), "control or result path differs")
    output.mkdir()
    seed = output / "Control.SLDPRT"
    copyfile(external_seed, seed)
    tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    expected = json.loads(specifications.read_bytes())
    report = {"schema": "kit.sw2026.sealed-import-geometry.v1", "job_sha256": checksum,
              "source_lock_receipt_sha256": SEALED_RECEIPT, "writer_revision": job["writer_revision"],
              "oracle_sha256": ORACLE, "oracle_file_version": "34.5.2.0604", "cases": {},
              "heldout_payloads_shared": 0, "complete_original_source_conversions": 0,
              "public_writer_qualified": False, "controls_healthy": False}
    if scene_mode:
        report["schema"] = "kit.sw2026.sealed-import-scene-text.v1"
        report["unqualified_source_domains"] = ["source tracking and provenance", "archived payload and system attributes"]
        if property_mode:
            report["schema"] = "kit.sw2026.sealed-import-property-owner.v1"
        else:
            report["unqualified_source_domains"].append("binary property manager")
    identities = []
    before = control(output, "ControlBefore", seed)
    faults = {}
    try:
        if before["passed"]:
            for slot in SLOTS:
                try:
                    arguments = slot, locks["sources"][slot], expected[slot], output
                    if scene_mode:
                        result, process_ids = evaluate_scene(*arguments, preserve_empty_file_owner=property_mode)
                    else:
                        result, process_ids = evaluate(*arguments)
                    report["cases"][slot] = result
                    identities.extend(process_ids)
                except Exception as exc:
                    faults[slot] = {"error_type": type(exc).__name__}
                    write_json(output / (slot + "Failure.json"), {"details": repr(exc)})
    finally:
        after = control(output, "ControlAfter", seed)
    for row in (before, after):
        if row["oracle_identity"]:
            identities.append(tuple(row["oracle_identity"][key] for key in ("process_id", "process_creation_filetime")))
    report["control_receipts"] = {"before": before["record_sha256"], "after": after["record_sha256"]}
    report["controls_healthy"] = bool(before["passed"] and after["passed"] and len(set(identities)) == len(identities))
    report["distinct_accepted_processes"] = len(set(identities))
    report["complete_heldout_geometry_lifecycles"] = len(report["cases"]) if report["controls_healthy"] else 0
    if scene_mode:
        report["complete_heldout_scene_text_lifecycles"] = report["complete_heldout_geometry_lifecycles"]
    if property_mode:
        report["complete_heldout_file_property_owner_lifecycles"] = report["complete_heldout_geometry_lifecycles"]
    report["faults"] = faults
    write_json(frozen_dir / "Result.json", report)
    print(json.dumps({"controls_healthy": report["controls_healthy"], "geometry_lifecycles": report["complete_heldout_geometry_lifecycles"]}))
    return int(report["complete_heldout_geometry_lifecycles"] != len(SLOTS))


if __name__ == "__main__":
    parser = ArgumentParser(description="Measure the sealed imported-body geometry scope without disclosing source inputs")
    parser.add_argument("job", type=Path)
    parser.add_argument("--job-sha256", required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.job.resolve(), args.job_sha256))
