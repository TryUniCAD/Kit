from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from subprocess import run
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from VerifyOriginBoxPlan import DIMENSIONS, MANIFEST, POSITIVE, ROOT, capture, pinned, refused


BASE = "862a73077a3520b697d97fef152e907c48e6fdad"
ORIGINAL_PLAN = "feb0a35f8975ee7d9a74e2eb416068e1337f7071cd2ec1c4bfdb524e5943ac61"
REFUSAL = "parameters disagree with their actual primitive owner"
ROLES = {
    "geometric_length_drivers": DIMENSIONS,
    "object_display_text": ("Label", "Label2"),
    "primitive_activation": ("Suppressed",),
    "fixed_source_visibility": ("Visibility",),
    "inactive_attachment": ("AttacherType", "AttacherEngine", "MapMode", "MapPathParameter", "MapReversed"),
    "no_base_algorithm_state": ("Refine", "FuzzyTolerance"),
}


def contrast(document, plan, field, attribute, alternative):
    (feature,) = document.feature_timeline
    (original,) = (value for value in document.parameters if value.attributes["freecad_path"] == field)
    value = replace(original.value, value=alternative) if attribute == "value" else alternative
    changed = replace(original, **{attribute: value})
    alternate = replace(
        document,
        parameters=tuple(changed if row is original else row for row in document.parameters),
        feature_timeline=(replace(feature, parameter_ids=tuple(changed.id if key == original.id else key for key in feature.parameter_ids)),),
    )
    alternate.assert_valid()
    assert alternate.brep is document.brep and alternate.brep_payloads == document.brep_payloads
    assert alternate.source == document.source and alternate.feature_timeline[0].definition is feature.definition
    return refused(plan, alternate, REFUSAL)


def worker(request):
    sys.path[:0] = [str(ROOT / "src"), str(Path(__file__).resolve().parent.parent)]
    from convert import open_document
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanOriginBox import PlanOriginBox
    from VerifyFreecadF14aIntact import no_runtime_io, wire

    source = Path(request["path"])
    raw = pinned(source, request["sha256"])
    document = open_document(source, strict=True, include_brep=True, include_tessellation=True)
    before = document.to_dict()
    restored = type(document).from_json(document.to_json(indent=None))
    assert restored.to_dict() == before
    for encoding in ("ascii", "latin-1", "utf-8", "utf-16-le"):
        lookup(encoding)
    with no_runtime_io():
        plan = PlanOriginBox(document)
        assert plan == PlanOriginBox(restored)
        findings = {
            label: contrast(document, PlanOriginBox, field, attribute, alternative)
            for label, field, attribute, alternative in (
                ("alternate_length_id_and_feature_alias", "Length", "id", "freecad:parameter:alternate:Length"),
                ("alternate_width_caption", "Width", "name", "Alternate.Width"),
                ("conflicting_attachment_mode", "MapMode", "value", 1),
                ("conflicting_visibility", "Visibility", "value", False),
            )
        }
    (feature,) = document.feature_timeline
    assert plan.SourceDocument is document and plan.SourceLineage.ProducerId == feature.id
    assert pinned(source, request["sha256"]) == raw and document.to_dict() == before
    classified = {path for paths in ROLES.values() for path in paths}
    typed = {parameter.attributes["freecad_path"]: parameter for parameter in document.parameters}
    missing = {"FuzzyTolerance"} if request["case"] == "recipe-1.0.2-F14a" else set()
    assert set(typed) == classified - missing
    assert tuple(typed[name] for name in DIMENSIONS) == plan.SourceDrivers
    return {
        "source_sha256": document.source.sha256,
        "body_owner": plan.SourceLineage.BodyId,
        "primitive_owner": feature.id,
        "source_parameter_count": len(typed),
        "source_parameter_inventory_sha256": sha256(wire(before["parameters"])).hexdigest(),
        "live_source_dimensions": {
            path: [typed[path].id, typed[path].value.value, typed[path].value.unit] for path in DIMENSIONS
        },
        "additional_source_values": {path: item.value.value for path, item in typed.items() if path not in DIMENSIONS},
        "refusals": findings,
        "verified_lineage_roles": len(plan.SourceLineage.Elements),
        "retained_payloads": len(document.brep_payloads),
        "strict_source_bytes_and_model_unchanged": True,
        "runtime_input_reads": 0,
    }


def measure(manifest, candidates):
    expected = json.loads(pinned(ROOT / "re/solidworks/measurements/2026/SdkFreecadF14aOriginPlan01.json", ORIGINAL_PLAN))
    observed = capture(manifest, candidates)
    assert observed["cases"] == expected["cases"] and observed["heldout_inputs_read"] == observed["new_native_processes"] == 0
    inputs = json.loads(pinned(manifest, MANIFEST))
    assert inputs["heldout_inputs"] == 0
    rows = {}
    for case in POSITIVE:
        (entry,) = (row for row in inputs["inputs"] if row["case"] == case)
        assert entry["sha256"] == expected["cases"][case]["source_sha256"]
        response = run(
            (sys.executable, "-I", "-B", __file__, "--worker"),
            input=json.dumps(entry), capture_output=True, text=True, timeout=90,
        )
        if response.returncode or response.stderr:
            raise ValueError(f"{case}: parameter owner probe refused\n{response.stderr}")
        rows[case] = json.loads(response.stdout)
    return {
        "schema": "kit.sw2026.f14a-source-parameter-owners.v1",
        "baseline_revision": BASE,
        "source_manifest_sha256": MANIFEST,
        "previous_origin_plan_receipt_sha256": ORIGINAL_PLAN,
        "previous_origin_plan_case_rows_exact": True,
        "source_literal_roles": ROLES,
        "cases": rows,
        "probe_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "recorded_source_files_sha256": observed["dependencies_sha256"],
        "historical_corpus_conversions_counted": 0,
        "heldout_inputs_read": 0,
        "independent_sdk_processes": observed["independent_sdk_processes"] + len(rows),
        "new_native_processes": 0,
        "intact_source_transfer_qualified": False,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("manifest", type=Path, nargs="?")
    parser.add_argument("candidates", type=Path, nargs="?")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    options = parser.parse_args()
    if options.worker:
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True, allow_nan=False))
    elif options.manifest is None or options.candidates is None or options.output is None:
        parser.error("manifest, candidates and an unused output are required")
    else:
        raw = (json.dumps(measure(options.manifest, options.candidates), indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
        with options.output.open("xb") as output:
            output.write(raw)
        print(sha256(raw).hexdigest())
