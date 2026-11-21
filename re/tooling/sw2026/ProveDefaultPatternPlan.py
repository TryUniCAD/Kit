from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path
from subprocess import check_output, run
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
TOOLS = HERE.parent / "linear_pattern"
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(TOOLS), str(TOOLS / "neutral"), str(TOOLS / "evaluation")]
BASE = "0fac2dce58f56ecf3d8625115a1fcd5645a3c5f3"
REFERENCE = "re/tooling/sw2026/linear_pattern/evaluation/PlanPatternEvaluation.py"
SOURCE_PATHS = (
    "src/convert/adapters/solidworks/Archive/Construction/Patterns/Input/PatAnnoBases.py",
    "src/convert/adapters/solidworks/Core/Preparation/Patterns/MakePatDefault.py",
    "src/convert/adapters/solidworks/Core/Preparation/Patterns/PlanLinPattern.py",
    "src/convert/adapters/solidworks/Core/Preparation/Patterns/ReadPatPresent.py",
)
HELDOUT_RECEIPT = "re/solidworks/measurements/2026/LocalLinearPatternDatumHeldoutNative01.json"
HELDOUT_PIN = "abaa363a2722c95166fe33cc668baf4555582b172e663ca67b42b775c9bacfb2"
DISCLOSED_RECEIPT = "re/solidworks/measurements/2026/SharedLinearPatternPlan01.json"
DISCLOSED_PIN = "edb8f7b9905eb8edd42195a4fc5741b2cf52a2588d3b423b0de1bf57ccdd64d3"


def require(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


def digest(raw):
    return sha256(raw).hexdigest()


def encode(data):
    return (json.dumps(data, sort_keys=True, allow_nan=False, indent=2) + "\n").encode()


def identities(data):
    return {name: {"bytes": len(raw), "sha256": digest(raw)} for name, raw in sorted(data.items())}


def current_style(recipe, bound_ids):
    from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PatDriveStyle import PatDriveStyle
    from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatAngleStyle import PatAngleStyle
    from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatPresentInput import PatPresentInput
    from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import AnnoViewInput

    angle, count, pitch = bound_ids
    label, catalog = recipe["plane"], recipe["annotation"]
    return PatPresentInput(
        PatAngleStyle(angle, label["annotation_view"], label["design_intent"], label["selected_leader"],
                      tuple(label["shifted_point_m"])),
        count, pitch,
        tuple(PatDriveStyle(row["name"], row["annotation_view"], tuple(row["label_m"]), row["design_intent"],
                            row["selected_leader"]) for row in recipe["pattern"]["styles"]),
        tuple(AnnoViewInput(row["name"], tuple(map(tuple, row["basis"]))) for row in catalog["views"]),
        catalog["active"], tuple(catalog["shown"]),
    )


def worker():
    from LocalPatternContainerProcess import audit, linked, observe_pattern, read_request, verify_keywords
    from EmitLocalPattern import emit_pattern
    from ProveSharedPatternPlan import normalized
    from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
    from convert.adapters.solidworks.Archive.Construction.Patterns.Input.LinPatternInput import LinPatternInput
    from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
    from convert.adapters.solidworks.Container.Format import KeywordsStream
    from convert.adapters.solidworks.Core.Preparation.Patterns.PlanLinPattern import PlanLinPattern
    from interchange import PlaneAxis
    from interchange.document.Behavior import DocumentIo
    from interchange.document.Models.DocumentModel import CadDocument
    from interchange.document.Validation import DocumentAssemblyValidate, DocumentFeatureValidate, DocumentReferenceValidate

    for text in ("utf-8", "utf-16-le", "latin-1", "us-ascii"):
        lookup(text)
    job = json.load(sys.stdin)
    explicit = current_style(job["expected"], job["parameter_ids"])
    target = SelfFileInput(**job["target"])
    audit.BeginBuild()
    wire = encode(job["document"])
    document = CadDocument.from_json(wire.decode())
    original = encode(document.to_dict())
    default = PlanLinPattern(document, target, None)
    require(type(document.feature_timeline[2].definition) is PlaneAxis and type(default) is LinPatternInput
            and PlanLinPattern(document, target) == default == PlanLinPattern(document, target, explicit)
            and encode(document.to_dict()) == original == wire, "default plan lost its typed source or explicit equivalent")
    submitted = encode(normalized(default))
    expected = encode(job["expected"])
    require(submitted == expected, "default plan does not reproduce the authored annotation and body recipe")
    refused = {}
    for name, changed, style, diagnostic in (
        ("unrepresented_presentation_metadata", replace(document, metadata={**document.metadata, "labels": []}), None, "ordinary neutral part name"),
        ("explicit_crossed_driver", document, replace(explicit, CountParamId=explicit.PitchParamId), "actual active parameter owners"),
    ):
        try:
            PlanLinPattern(changed, target, style)
        except ValueError as error:
            require(diagnostic in str(error), "default refusal moved to another validation boundary")
            refused[name] = diagnostic
        else:
            raise ValueError("default or explicit presentation admitted an invalid input")
    planned_input = read_request(json.loads(submitted))
    reference_input = read_request(json.loads(expected))
    _, streams, payload = emit_pattern(*planned_input)
    _, reference_streams, reference_payload = emit_pattern(*reference_input)
    require(streams == reference_streams and payload == reference_payload and len(streams) == 10,
            "model-derived presentation changed the complete encoded part")
    link, headers = linked(payload, streams)
    actual = observe_pattern(link, headers, planned_input)
    verify_keywords(streams[KeywordsStream], planned_input, actual)
    principal = PrincipalFrame("y")
    top_basis = (principal.AxisU, principal.AxisV, principal.NormalValue)
    top, back = explicit.AnnoValues
    require(top_basis == top.BasisValue and encode(top_basis) != encode(top.BasisValue),
            "principal Top and canonical annotation Top should differ only by the signs of zero")
    alternate = replace(explicit, AnnoValues=(replace(top, BasisValue=top_basis), back))
    alternate_plan = PlanLinPattern(document, target, alternate)
    alternate_request = read_request(json.loads(encode(normalized(alternate_plan))))
    _, alternate_streams, alternate_payload = emit_pattern(*alternate_request)
    changed = sorted(name for name, raw in streams.items() if raw != alternate_streams[name])
    require(changed == ["Contents/Config-0"] and payload != alternate_payload,
            "the signed-zero Top contrast did not isolate the expected annotation stream")
    require(not audit.DeniedReads and not {"Swapp", "pythoncom", "win32com", "FreeCAD", "adsk"} & sys.modules.keys(),
            "default planning or emission attempted a CAD or input read")
    print(json.dumps({"recipe_sha256": digest(submitted), "complete_file_sha256": digest(payload),
                      "complete_bytes": len(payload), "streams": identities(streams), "exact_typed_stream_replays": 9,
                      "annotation_order": [row.NameValue for row in default.AnnoValues],
                      "parameter_ids": job["parameter_ids"], "driver_order": actual["driver_order"],
                      "label_points_m": {row.NameValue: row.LabelValue for row in default.StyleValues},
                      "guarded_runtime_reads": len(audit.DeniedReads), "refused": refused,
                      "principal_top_signed_zero_contrast": {"changed_streams": changed,
                                                             "complete_file_sha256": digest(alternate_payload)}}, sort_keys=True))


def modeled_defaults(authored):
    from PlanPatternEvaluation import BACK, TOP
    from ProveSharedPatternPlan import typed_recipe

    modeled = typed_recipe(authored)
    seed = modeled["seed"]["seed"]["bounds_m"]
    centre = [(low + high) / 2.0 for low, high in zip(*seed, strict=True)]
    centre[2] = 0.0
    origins = {"D1": centre, "D2": seed[0]}
    modeled["plane"].update(annotation_view="*Back", design_intent=True, selected_leader=0, shifted_point_m=[0.0, 0.0, 0.0])
    modeled["annotation"] = {"views": [{"name": "*Top", "basis": TOP}, {"name": "*Back", "basis": BACK}],
                            "active": None, "shown": [None]}
    modeled["pattern"]["styles"] = [
        {"name": label, "annotation_view": "*Back" if label == "D1" else None,
         "label_m": origins.get(label, [0.0, 0.0, 0.0]), "design_intent": True, "selected_leader": 0}
        for label in ("D1", "D3", "D2", "D4", "D5", "D6")
    ]
    return modeled


def rename_ids(value, aliases):
    if type(value) is dict:
        return {key: rename_ids(row, aliases) for key, row in value.items()}
    if type(value) is list:
        return [rename_ids(row, aliases) for row in value]
    return aliases.get(value, value) if type(value) is str else value


def verify_old_receipts():
    historical = {
        name: digest((ROOT / name).read_bytes()) for name in (REFERENCE, HELDOUT_RECEIPT, DISCLOSED_RECEIPT)
    }
    require(historical[HELDOUT_RECEIPT] == HELDOUT_PIN and historical[DISCLOSED_RECEIPT] == DISCLOSED_PIN
            and check_output(("git", "show", BASE + ":" + REFERENCE), cwd=ROOT) == (ROOT / REFERENCE).read_bytes(),
            "existing source rule or comparison evidence changed")
    return historical


def measure(disclosed, output):
    from ProveNeutralPattern import EXPECTED, author_document, validated_disclosed

    previous = verify_old_receipts()
    _, frozen = validated_disclosed(disclosed)
    results = {}
    for index, (name, records) in enumerate(sorted(frozen.items())):
        modeled = records["original"]["modeled_input"]
        request = author_document(modeled)
        document = json.loads(encode(request.document.to_dict()))
        angle, count, pitch = (request.presentation.angle.parameter_id, request.presentation.count_parameter_id,
                               request.presentation.pitch_parameter_id)
        if index:
            aliases = {angle: "angle/rotating-control", count: "repetition/quantity-control", pitch: "layout/pitch-control"}
            document = rename_ids(document, aliases)
            angle, count, pitch = (aliases[key] for key in (angle, count, pitch))
        data = {"document": document, "target": asdict(request.output), "parameter_ids": (angle, count, pitch),
                "expected": modeled_defaults(modeled)}
        received = run((sys.executable, "-I", "-B", str(HERE), "--worker"), cwd=ROOT, input=encode(data),
                       capture_output=True, timeout=90, check=False)
        require(received.returncode == 0 and not received.stderr,
                "default worker refused " + name + "\n" + received.stderr.decode())
        result = json.loads(received.stdout)
        require(result["parameter_ids"] == list(data["parameter_ids"]) and result["guarded_runtime_reads"] == 0,
                "default worker did not own the expected local parameter bindings")
        results[name] = {**result, "input_sha256": digest(encode(data)), "source_recipe_path_case": name}
    require(len(results) == 2 and len({row["complete_file_sha256"] for row in results.values()}) == 2
            and len({tuple(row["label_points_m"]["D1"]) for row in results.values()}) == 2,
            "expected two independent parts with distinct generated display points")
    report = {
        "schema": "kit.sw2026.default-oblique-pattern-presentation.v1", "base_revision": BASE,
        "previous_authority": previous, "disclosed_fixture_authority": EXPECTED,
        "cases": results, "guarded_worker_processes": len(results),
        "source_sha256": {name: digest((ROOT / name).read_bytes()) for name in SOURCE_PATHS},
        "proof_sha256": digest(HERE.read_bytes()),
        "native_processes_started": 0, "protected_inputs_read": 0, "new_native_acceptance": 0,
        "public_writer_registered": False,
    }
    raw = encode(report)
    with output.open("xb") as handle:
        handle.write(raw)
    print(json.dumps({"receipt_sha256": digest(raw), "complete_typed_cases": len(results)}, sort_keys=True))


def main():
    if sys.argv[1:] == ["--worker"]:
        worker()
        return
    parser = ArgumentParser(description="Verify the shared pattern default presentation on two disclosed neutral inputs")
    parser.add_argument("--disclosed", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    measure(args.disclosed.resolve(strict=True), args.output)


if __name__ == "__main__":
    main()
