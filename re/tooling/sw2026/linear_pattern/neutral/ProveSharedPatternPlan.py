from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from subprocess import check_output, run
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent), str(HERE.parents[1])]
BASE = "45e4f8b83a674913d7a9c0349290a26fd10e0773"
PLANNER = "src/convert/adapters/solidworks/Core/Preparation/Patterns"
INPUTS = "src/convert/adapters/solidworks/Archive/Construction/Patterns/Input"
ROLES = ("original", "pitch_only", "count_only")
APPLICATIONS = {"FreeCAD", "FreeCADGui", "Part", "adsk", "pythoncom", "win32com"}


def require(value, message):
    if not value:
        raise ValueError(message)


def encode(data):
    return (json.dumps(data, sort_keys=True, allow_nan=False, indent=2) + "\n").encode()


def digest(data):
    return sha256(data).hexdigest()


def normalized(plan):
    def box(input_value):
        return {"sketch": input_value.SketchName, "feature": input_value.FeatureName, "bounds_m": input_value.BoundsValue}

    stock, angle = plan.StockValue, plan.AngleValue
    return {
        "seed": {"name": stock.NameValue, "configuration": stock.ConfigName, "path": stock.PathValue,
                 "epoch": stock.SavedAt, "plate": box(stock.PlateValue), "seed": box(stock.SeedValue)},
        "axis": plan.HingeName,
        "plane": {"name": angle.NameValue, "angle_rad": angle.AngleValue, "reverse": angle.Reversed,
                  "annotation_view": angle.AnnotationName, "design_intent": angle.DesignIntent,
                  "selected_leader": angle.SelectedLeader, "shifted_point_m": angle.ShiftValue},
        "annotation": {"views": [{"name": row.NameValue, "basis": row.BasisValue} for row in plan.AnnoValues],
                       "active": plan.ActiveAnno, "shown": plan.ShownAnnos},
        "pattern": {"name": plan.NameValue, "count": plan.CountValue, "pitch_m": plan.PitchValue,
                    "reverse": plan.Reversed, "styles": [
                        {"name": style.NameValue, "annotation_view": style.AnnotationName, "label_m": style.LabelValue,
                         "design_intent": style.DesignIntent, "selected_leader": style.SelectedLeader}
                        for style in plan.StyleValues]},
    }


def worker():
    from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
    from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PatDriveStyle import PatDriveStyle
    from convert.adapters.solidworks.Archive.Construction.Patterns.Input.LinPatternInput import LinPatternInput
    from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatAngleStyle import PatAngleStyle
    from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatPresentInput import PatPresentInput
    from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import AnnoViewInput
    from convert.adapters.solidworks.Core.Preparation.Patterns.PlanLinPattern import PlanLinPattern
    from interchange import PlaneAxis
    from interchange.document.Behavior import DocumentIo
    from interchange.document.Models.DocumentModel import CadDocument
    from interchange.document.Validation import DocumentAssemblyValidate, DocumentFeatureValidate, DocumentReferenceValidate
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

    for codec in ("utf-8", "utf-16-le", "latin-1", "us-ascii"):
        lookup(codec)
    value = json.load(sys.stdin)
    authored = value["presentation"]
    label = authored["angle"]
    present = PatPresentInput(
        PatAngleStyle(label["parameter_id"], label["annotation_view"], label["design_intent"],
                      label["selected_leader"], tuple(label["shifted_point_m"])),
        authored["count_parameter_id"], authored["pitch_parameter_id"],
        tuple(PatDriveStyle(row["name"], row["annotation_view"], tuple(row["label_m"]),
                            row["design_intent"], row["selected_leader"]) for row in authored["styles"]),
        tuple(AnnoViewInput(row["name"], tuple(map(tuple, row["basis"]))) for row in authored["views"]),
        authored["active"], tuple(authored["shown"]),
    )
    target = SelfFileInput(value["target"]["PathName"], value["target"]["SavedAt"])
    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    sys.addaudithook(audit.InspectEvent)
    audit.BeginBuild()
    document_bytes = encode(value["document"])
    document = CadDocument.from_json(document_bytes.decode())
    plan = PlanLinPattern(document, target, present)
    require(type(plan) is LinPatternInput and type(document.feature_timeline[2].definition) is PlaneAxis,
            "the shared planner did not use the public neutral axis and typed archive recipe")
    require(encode(document.to_dict()) == document_bytes, "planner changed its portable model wire")
    require(not audit.DeniedReads and not {name.split(".")[0] for name in sys.modules} & APPLICATIONS,
            "shared preparation attempted a data read or imported a CAD application")
    recipe = normalized(plan)
    print(json.dumps({"recipe": recipe, "recipe_sha256": digest(encode(recipe)), "guarded_input_reads": len(audit.DeniedReads),
                      "public_axis_type": True, "portable_doc_sha256": digest(document_bytes),
                      "created_native_files": 0, "imported_cad_modules": 0}, sort_keys=True, allow_nan=False))


def execute(value):
    return run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=encode(value), cwd=ROOT,
               capture_output=True, timeout=60, check=False)


def typed_recipe(expected):
    result = deepcopy(expected)
    bounds = result["seed"]["plate"]["bounds_m"]
    require(bounds[0] == [0, 0, 0] and all(type(value) in (int, float) for value in bounds[0]),
            "the frozen source lost its model origin")
    bounds[0] = [float(value) for value in bounds[0]]
    return result


def faults(original):
    cases = (
        ("extra_metadata", ("document", "metadata", "hinge"), "recorded fallback", "ordinary neutral part name"),
        ("no_axis", ("document", "feature_timeline", "$tuple", 2, "definition"), None, "typed finite plane intersection axis"),
        ("no_finite_trim", ("document", "feature_timeline", "$tuple", 2, "definition", "end_mm", "z"),
         -2.0, "directed first plane trim"),
        ("crossed_seed", ("document", "selections", "$tuple", 6, "path", "$tuple", 0, "entity_id"),
         "feature/plate", "exact local body owner"),
        ("wrong_count", ("document", "parameters", "$tuple", 4, "value", "value"), 5, "drivers disagree"),
        ("absent_outline", ("document", "sketches", "$tuple", 0, "closed_profile_entity_ids", "$tuple"),
         [], "closed line loop"),
        ("wrong_body", ("document", "bodies", "$tuple", 0, "final_feature_id"), "feature/seed", "final neutral body"),
        ("wrong_topology", ("document", "bodies", "$tuple", 0, "topology", "face_count"), 7, "final neutral body"),
        ("changed_configuration", ("document", "configurations", "$tuple", 0, "active"),
         False, "unsupported configuration state"),
        ("nonlocal_target", ("target", "PathName"), r"C:\KitGeneratedLocalPattern\Unused.SLDPRT", "exact authored native basename"),
        ("crossed_style_owner", ("presentation", "count_parameter_id"), "parameter/pitch", "presentation is not bound"),
        ("shifted_angle_label", ("presentation", "angle", "shifted_point_m", 1), 0.01, "zero shifted point"),
        ("invalid_back_frame", ("presentation", "views", 0, "basis"),
         [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], "actual Back catalog"),
        ("duplicate_shown", ("presentation", "shown"), [None, None], "actual Back catalog"),
        ("wrong_pitch_style", ("presentation", "styles", 1, "label_m", 0), 0.01, "unassigned pitch profile"),
    )
    for name, path, replacement, diagnostic in cases:
        value = deepcopy(original)
        owner = value
        for key in path[:-1]:
            owner = owner[key]
        owner[path[-1]] = replacement
        yield name, value, diagnostic
    value = deepcopy(original)
    value["document"]["parameters"]["$tuple"][4]["value"]["value"] = 9
    value["document"]["feature_timeline"]["$tuple"][4]["definition"]["instance_count"] = 9
    yield "excess_instances", value, "two to eight instances"


def check_frozen():
    require(not check_output(("git", "diff", "--name-only", BASE, "--", "re/tooling/sw2026/linear_pattern",
                              "src/interchange", "tests/Convert/Solidworks/Research/ConstructionGuard.py",
                              ":(exclude)" + HERE.relative_to(ROOT).as_posix()), cwd=ROOT),
            "historical proof chain, portable schema or process guard changed")
    return {
        str(path.relative_to(ROOT)): digest(path.read_bytes())
        for folder in (ROOT / PLANNER, ROOT / INPUTS)
        for path in sorted(folder.glob("*.py"))
    }


def supervise(disclosed, output):
    from ProveNeutralPattern import EXPECTED, author_document, checked_file, validated_disclosed

    require(not output.exists(), "choose a fresh shared planner receipt")
    sources = check_frozen()
    packet, frozen = validated_disclosed(disclosed)
    cases, contrasting, original = {}, {}, None
    for name, records in sorted(frozen.items()):
        require(set(records) == set(ROLES), "expected all three exact disclosed phases")
        case = {}
        for role in ROLES:
            prior = records[role]
            authored = author_document(prior["modeled_input"])
            expected = typed_recipe(prior["modeled_input"])
            data = json.loads(encode({"document": authored.document.to_dict(), "target": asdict(authored.output),
                                      "presentation": asdict(authored.presentation)}))
            measured = execute(data)
            require(measured.returncode == 0 and not measured.stderr,
                    "guarded shared planner refused " + name + "/" + role + "\n" + measured.stderr.decode())
            proof = json.loads(measured.stdout)
            require(proof.pop("recipe") == expected and proof["recipe_sha256"] == digest(encode(expected))
                    and proof["public_axis_type"] and proof["guarded_input_reads"] == proof["created_native_files"] == 0,
                    "shared typed recipe differs from the frozen model authority " + name + "/" + role)
            case[role] = {**proof, "request_sha256": digest(encode(data)),
                          "prior_complete_file_sha256": prior["native_container"]["sha256"]}
            if role == "original":
                fixture = "Packet/" + name + ".SLDPRT"
                require(digest(checked_file(disclosed, fixture, packet["files"][name + ".SLDPRT"]))
                        == prior["native_container"]["sha256"], "disclosed original custody differs")
                original = original or data
            else:
                base_pattern = records["original"]["modeled_input"]["pattern"]
                change, = (key for key, old in base_pattern.items() if expected["pattern"][key] != old)
                require(change == ("pitch_m" if role == "pitch_only" else "count"),
                        "a disclosed edit changed an unrelated modeled field")
        cases[name] = case
    require(len(cases) == 2 and original is not None, "both expected independent disclosed inputs are required")
    for name, changed, diagnostic in faults(original):
        refused = execute(changed)
        require(refused.returncode != 0 and not refused.stdout and diagnostic in refused.stderr.decode(),
                "wrong refusal for " + name + "\n" + refused.stderr.decode())
        contrasting[name] = diagnostic
    require(sources == check_frozen(), "planner changed during the guarded comparison")
    report = {
        "schema": "kit.sw2026.shared-oblique-pattern-plan.v1", "base_revision": BASE,
        "disclosed_authority": EXPECTED, "typed_projection_cases": cases, "checked_refusals": contrasting,
        "isolated_processes": len(contrasting) + len(cases) * len(ROLES),
        "source_sha256": sources, "proof_sha256": digest(HERE.read_bytes()),
        "historical_proof_unchanged": True, "heldout_inputs_read": 0, "native_processes_started": 0,
        "public_writer_registered": False, "new_native_acceptance": 0,
        "footprint_check": "owned by later shared geometry before complete construction",
    }
    raw = encode(report)
    with output.open("xb") as handle:
        handle.write(raw)
    print(json.dumps({"receipt_sha256": digest(raw), "typed_recipes": len(cases) * len(ROLES),
                      "checked_refusals": len(contrasting)}, sort_keys=True))


def main():
    if sys.argv[1:] == ["--worker"]:
        worker()
        return
    parser = ArgumentParser(description="Compare the shared portable pattern planner with the frozen disclosed model")
    parser.add_argument("--disclosed", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    supervise(args.disclosed.resolve(strict=True), args.output)


if __name__ == "__main__":
    main()
