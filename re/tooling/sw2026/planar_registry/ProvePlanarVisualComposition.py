from argparse import ArgumentParser
from base64 import b64encode
from codecs import lookup
from collections import Counter
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
from tarfile import open as open_tar
from tempfile import TemporaryDirectory


TOOL = Path(__file__).resolve()
sys.path.insert(0, str(TOOL.parent))
from PlanarRegistryBuild import ROOT, artifact, file_sha, load, require, write
from ProvePlanarAssemblyIdentity import bind_sdk, canonical, dispatch as identity_dispatch, excluded_modules


BASE = "6992314aee87ce890cdb6e46436521ad081c25cf"
IDENTITY = "e1af358c410afaf15a70100111f4e4aa8183ec11de97ae68fb07a983677c6671"
LABELS = "fb68f130ad521ca7473c6f3f239a71a276ccb2318c75586b1eb63de930965f55"
VISUALS = "ThirdPtyStore/VisualStates"
TREE = "swXmlContents/COMPINSTANCETREE"
CMGR = "Contents/CMgr"
SHAPE_REFUSAL = "assembly root contains unprojected model content"
FAULTS = {
    "duplicate-member": "assembly display state must bind each actual occurrence exactly once",
    "reordered-member": "planar visibility must retain the actual occurrence order",
    "mixed-visibility": "planar visibility requires one all-visible default state",
    "detached-stamp": "assembly visual context requires the fresh flag-zero links",
    "foreign-mate": "planar visibility requires the actual ordered aligned and distance mates",
    "unbound-child-store": "planar child visual store has no modeled appearance association",
    "missing-child-store": "planar child visual store does not match its model owners",
    "foreign-renderer": "part self visibility cannot project populated RealView or DSPBR appearance",
    "mismatched-creation-log": "part visual reference lost its actual feature or creation owner",
    "unaligned-visual-state": "part self visibility requires the default constructor appearance intent",
}


def inject(fault, bundle, recipe):
    from convert.adapters.solidworks.Archive.Construction.Header.MakeRootLog import MakeRootLog

    child = bundle.ChildValue
    if fault == "detached-stamp":
        context = bundle.StateValue.CurrentConfig.FieldsValue["fce8"][1]["o"].FieldsValue["f10"]
        context.FieldsValue["f30"] += 1
    elif fault == "foreign-mate":
        bundle.MateValues[1].FieldsValue["owner"] = bundle.StateValue.RootValue
    elif fault == "unbound-child-store":
        child = replace(child, SelfView=None)
    elif fault == "missing-child-store":
        child = replace(child, StreamsValue={key: value for key, value in child.StreamsValue.items() if key != VISUALS})
    elif fault == "foreign-renderer":
        child.SystemValue.RootValue.FieldsValue["f78"].FieldsValue["has88"] = 1
    elif fault == "mismatched-creation-log":
        log = child.HeaderValue.FieldsValue["f20"].FieldsValue
        log["items"] = (*log["items"], MakeRootLog(child.ProfileValue.ProfileValue, recipe.HeaderValue))
    elif fault == "crossed-render-cursor":
        child.DefinitionValue.DocumentValue.FieldsValue["f1110"]["f08"] += 1
    elif fault == "aliased-shader":
        model = child.SystemValue.RootValue.FieldsValue["f78"]
        config = child.CurrentConfig.FieldsValue["f78"]
        config.FieldsValue["f88"] = model.FieldsValue["f88"]
    return child


def make_guard():
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    sys.addaudithook(audit.InspectEvent)

    def external_attempt(event, args):
        if event.startswith(("socket.", "ctypes.")):
            audit.DeniedReads.append(event)
            raise PermissionError("planar visual assembly attempted external execution")

    sys.addaudithook(external_attempt)
    for encoding in ("utf-16-le", "utf-8", "utf-8-sig", "latin-1", "ascii"):
        lookup(encoding)
    for name in (
        "RectanglePresentation", "para.concentric.MakeDisplayTree",
        "convert.adapters.solidworks.Archive.Config.WriteConfigMut",
        "convert.adapters.solidworks.Archive.Resolved.WriteResolMut",
        "convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadLineDims",
        "interchange.document.Behavior.DocumentIo", "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentValidate", "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate", "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(name)
    return audit


def compose(root, request, deliver=False):
    bind_sdk(root)
    from CheckOriginalPlanarMethod import no_recorded_state
    from PlanarAssemblyIdentity import observe, xml_display
    from PlanarRootProjection import prepare_system
    from PlanarVisualOwners import child_store, parent_store
    from ProvePlanarRootProjection import observe_archive
    from ProveSketchLabelIntent import audit_link
    from SketchLabelIntent import make_child
    from para.concentric.ProveVisualStateStore import registry
    from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.AsmDisplayIn import AsmDisplayIn
    from convert.adapters.solidworks.Archive.Construction.Assembly.EmitAsmStreams import EmitAsmStreams
    from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.MakePlanarGroup import MakePlanarGroup
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from interchange.serialization.Deserialize import FromData

    require(set(request) == {"document", "labels", "native_parent", "event", "parent_system", "model_name",
                            "display", "self_appearance", "fault"},
            "guarded writer requires explicit neutral assembly and presentation inputs")
    no_recorded_state(request)
    document = FromData(request["document"])
    document.assert_valid()
    require(not any(key.startswith("kit.research_") for key in document.metadata),
            "a research source status cannot authorize native output")
    self_view = None
    rendered = None
    confirm = None
    if request["self_appearance"] is not None:
        from convert.adapters.solidworks.Archive.Construction.Part.Displays.PartSelfView import PartSelfView
        view = request["self_appearance"]
        require(set(view) == {"state", "appearance"}, "part self appearance request is incomplete")
        appearance = view["appearance"]
        if type(appearance) is dict:
            from PlanarRendererInput import confirm_look, from_json
            rendered = appearance
            confirm = confirm_look
            appearance = from_json(rendered)
        self_view = PartSelfView(view["state"], appearance)
    view = request["display"]
    intent = None
    if view is not None:
        require(set(view) == {"name", "visibility"}, "assembly display request is incomplete")
        intent = (AsmDisplayIn(view["name"], tuple(tuple(row) for row in view["visibility"])),)
    reg = registry()
    audit = make_guard()
    audit.BeginBuild()
    path, event = request["native_parent"], request["event"]
    plan, child = make_child(document, path, event, request["labels"], self_view)
    recipe = plan.RootRecipe
    if request["parent_system"] is not None:
        recipe = replace(recipe, SystemValue=prepare_system(recipe.SystemValue, request["parent_system"], event))
    if request["model_name"] is not None:
        recipe = replace(recipe, ModelName=request["model_name"])
    arguments = child, recipe, plan.Occurrences, plan.MatesValue, plan.FixedIndex
    fault = request["fault"]
    if fault in {"detached-stamp", "foreign-mate", "unbound-child-store", "missing-child-store",
                 "foreign-renderer", "mismatched-creation-log", "crossed-render-cursor", "aliased-shader"}:
        base = MakePlanarGroup(*arguments)
        child = inject(fault, base, recipe)
        EmitAsmStreams(base.StateValue, child, recipe, (base.HeaderValue, base.TopHeader),
                       base.OccurrenceValues, base.MateValues, DisplayValues=intent)
        raise RuntimeError("injected unsupported owner reached a generated output")
    bundle = MakePlanarGroup(*arguments) if intent is None else MakePlanarGroup(*arguments, DisplayValues=intent)
    parent = SldprtArchive.from_bytes(bundle.BytesValue)
    child_file = SldprtArchive.from_bytes(child.BytesValue)
    identity = observe(parent, stem=document.metadata["name"], destination=path)
    mates = tuple(row.name for row in document.assembly.mates)
    root_owners = observe_archive(bundle, mates, request["parent_system"] is not None)
    linked = audit_link(bundle)
    result = {}
    if intent is not None:
        expected_xml, _ = xml_display(bundle, view)
        require(parent.require(TREE) == expected_xml and identity["view"] is not None,
                "the actual assembly emitter differs from the independent typed display tree")
        result["parent_store"] = parent_store(parent, reg)
    if self_view is not None:
        result["child_store"] = child_store(child_file, reg, rich=rendered is not None)
    if confirm is not None:
        result["renderer"] = confirm(child_file, reg, rendered)
    require(bundle.ChildValue is child and not audit.DeniedReads and not excluded_modules(),
            "composition did not keep its actual neutral child and zero-runtime-input boundary")
    if deliver:
        result["generated_bytes"] = {"parent": b64encode(bundle.BytesValue).decode("ascii"),
                                     "child": b64encode(child.BytesValue).decode("ascii")}
    return {"pid": os.getpid(), "runtime_input_reads": len(audit.DeniedReads), "identity": identity,
            "occurrences": root_owners["occurrences"], "ordered_mates": root_owners["ordered_mates"],
            "mate_ids": root_owners["mate_ids"],
            "parent": artifact(bundle), "child": artifact(child), "labels": linked["actual"], **result}


def run(root, payload, error=None):
    result = subprocess.run((sys.executable, "-I", "-B", str(TOOL), "build", "--root", str(root)),
                            input=canonical(payload), capture_output=True, check=False, timeout=120)
    if error is not None:
        require(result.returncode != 0 and not result.stdout and error in result.stderr.decode(errors="replace")
                and b"PermissionError" not in result.stderr, "rejected at an unrelated boundary: " + result.stderr.decode(errors="replace"))
        return error
    require(result.returncode == 0, result.stderr.decode(errors="replace"))
    return json.loads(result.stdout)


def source_request(row, prior_case, identity_case):
    from PlanarAssemblyIdentity import observe, request_view
    from PlanarPriorAdmission import source_intent
    from PlanarRootProjection import project
    from PlanarSourceLabels import project_labels
    from PlanarVisualOwners import DISPLAY, child_store, parent_store, source_definition
    from ProvePlanarMateGroup import checked
    from ProvePlanarSourceLabels import refusal
    from ProveSketchLabelIntent import payload
    from para.concentric.ProveVisualStateStore import registry
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.AssemblyWriting.CheckAsmShape import CheckAsmShape
    from interchange import CadDocument

    paths = [Path(row[role]) for role in ("parent", "child")]
    parent_raw, child_raw = (checked(path, row[role + "_sha256"]) for path, role in zip(paths, ("parent", "child"), strict=True))
    author = json.loads(checked(paths[0].parent / "Record.json", row["native_record_sha256"]))
    source_read = identity_dispatch("read", ROOT, row)
    source = CadDocument.from_json(canonical(source_read["document"]).decode())
    neutral, previous = source_intent(source, author["job"]["case"], child_raw)
    labels, _ = project_labels(source.assembly.documents[0].document, child_raw, neutral.assembly.documents[0].document,
                               prior_case["exact_source_display"])
    system, _ = project(source, neutral, parent_raw, previous["source_intent"]["assembly"]["system"])
    parent, child = (SldprtArchive.from_bytes(raw) for raw in (parent_raw, child_raw))
    owners = observe(parent, stem=paths[0].stem)
    display = request_view(source, owners)
    request = {**payload(neutral, labels), "parent_system": system, "model_name": owners["native_model"],
               "display": display, "self_appearance": {"state": DISPLAY, "appearance": "constructor"}, "fault": None}
    require(all(row[key].encode() not in canonical(request) for key in ("parent_sha256", "child_sha256")),
            "the guarded request contains an original CAD identity")
    reg = registry()
    source_parent, source_child = parent_store(parent, reg), child_store(child, reg, rich=True)
    for role, observed in (("parent", source_parent), ("child", source_child)):
        require(observed["sha256"] == identity_case["source_visual_owners"][role]["sha256"],
                "native visual stream differs from its previous locked audit")
    seals = {key: row[key] for key in ("parent_sha256", "child_sha256", "native_record_sha256")}
    require(source_child["appearance_roles"]["holder"]["realview_id"] != source_child["appearance_roles"]["model"]["realview_id"],
            "the child part self holder was conflated with the model appearance")
    return request, source_read["pid"], {"source_locks": seals, "parent_store": source_parent, "child_store": source_child,
                 "mate_ids": [[row.name, int(row.provenance.native_id)] for row in source.assembly.mates],
                 "definition": source_definition(child), "whole_source_guard": refusal(CheckAsmShape, (source,), SHAPE_REFUSAL)}


def change_set(first, second):
    return sorted(key for key in first.keys() | second.keys() if first.get(key) != second.get(key))


def compare(control, parent_only, full, repeated, request):
    def stable(data):
        return {key: val for key, val in data.items() if key != "pid"}

    require(stable(full) == stable(repeated), "independent neutral constructions differ")
    require(parent_only["child"] == control["child"] and full["parent"] == parent_only["parent"]
            and change_set(control["parent"]["streams"], full["parent"]["streams"]) == sorted((TREE, VISUALS))
            and change_set(control["child"]["streams"], full["child"]["streams"]) == [CMGR, VISUALS],
            "display changed an unrelated parent, child, or link stream")
    require(all(row["occurrences"] == control["occurrences"] and row["ordered_mates"] == control["ordered_mates"]
                and row["mate_ids"] == control["mate_ids"]
                and row["labels"] == control["labels"] for row in (parent_only, full, repeated)),
            "display changed placement, mate order or actual child dimension ownership")
    infos = full["identity"]["view"]
    require(infos["StateName"] == request["display"]["name"]
            and [[row["NativeName"], row["Visible"]] for row in infos["MemberValues"]]
                == [list(row) for row in request["display"]["visibility"]]
            and [row["FeatureId"] for row in infos["MemberValues"]][::-1] ==
                [row[0] for row in full["parent_store"]["occurrence_rows_in_wire_order"]],
            "the two generated parent display stores do not share actual visible occurrences")
    return stable(full)


def source_owner_boundary(source, generated):
    old, new = (entry["parent_store"] for entry in (source, generated))
    require(old["occurrence_rows_in_wire_order"] == new["occurrence_rows_in_wire_order"]
            and old["configuration_id"] == new["configuration_id"]
            and source["mate_ids"] == [list(row) for row in zip(generated["ordered_mates"], generated["mate_ids"], strict=True)]
            and new["bytes"] - old["bytes"] == 2 * new["parent_header_locator_codepoints"],
            "parent occurrence or mate identities do not match the disclosed graph")
    bindings = {}
    for store, key in (("parent_store", "plane_keys"), ("child_store", "linked_features")):
        first, second = (entry[store][key] for entry in (source, generated))
        require([(row[1], row[3]) for row in first] == [(row[1], row[3]) for row in second],
                "visual feature roles or flags changed across the independent owner graphs")
        bindings[store] = [[before[1], before[0], after[0], before[2], after[2]]
                           for before, after in zip(first, second, strict=True)]
    return bindings


def independently_authored():
    from PlanarVisualOwners import DISPLAY
    from ProveSketchLabelIntent import fixture, label_rows, payload

    document = fixture((0.0647, 0.0259, 0.0143))
    graph = document.assembly
    link, = graph.documents
    config, = link.document.configurations
    child = replace(link.document, configurations=(replace(config, name="Default"),))
    defs = tuple(replace(row, configuration_name="Default") if row.document_id else row for row in graph.definitions)
    numeric_names = ("PublicDatumPrism-14", "PublicDatumPrism-8")
    instances = tuple(replace(row, configuration_name="Default", name=name) for row, name in zip(graph.instances, numeric_names, strict=True))
    document = replace(document, assembly=replace(graph, documents=(replace(link, document=child),), definitions=defs, instances=instances))
    labels = label_rows(child, ((0.027, -0.013, 0.007), (0.080, 0.012, -0.005)), (True, False))
    return {**payload(document, labels), "parent_system": None, "model_name": "IndependentDisplay",
            "display": {"name": "Display State-1", "visibility": [[name, True] for name in numeric_names]},
            "self_appearance": {"state": DISPLAY, "appearance": "constructor"}, "fault": None}


def refusal_request(request, fault):
    broken = json.loads(canonical(request))
    broken["fault"] = fault
    if fault == "duplicate-member":
        broken["display"]["visibility"][1] = broken["display"]["visibility"][0]
    elif fault == "reordered-member":
        broken["display"]["visibility"].reverse()
    elif fault == "mixed-visibility":
        broken["display"]["visibility"][0][1] = False
    elif fault == "unaligned-visual-state":
        broken["self_appearance"]["state"] = "ForeignPartState"
    return broken


def prove(disclosed, output):
    bind_sdk(ROOT)
    from PlanarVisualOwners import COMPOUND
    from ProvePlanarMateGroup import checked, source_cases

    measures = ROOT / "re/solidworks/measurements/2026"
    identity = load(measures / "SdkPlanarAssemblyIdentity01.json", IDENTITY)
    prior = load(measures / "SdkPlanarPriorSourceAdmission01.json", LABELS)
    output.mkdir()
    radial = ROOT / "re/tooling/sw2026/para/concentric/VerifySdkVisualStore.py"
    radial_compare = subprocess.check_output((sys.executable, "-I", "-B", str(radial),
                                             "verify", str(output / "RadialControl.json")), timeout=180)
    radial_proof = json.loads(radial_compare)
    require(radial_proof["passed"] and radial_proof["native_exact"] and radial_proof["refusals"] == 13,
            "the unchanged radial disclosure and refusals did not reproduce")
    cases, processes = {}, []
    with TemporaryDirectory(prefix="KitPlanarBase") as folder:
        baseline = Path(folder).resolve()
        frozen = subprocess.check_output(("git", "archive", BASE, "src"), cwd=ROOT)
        with open_tar(fileobj=BytesIO(frozen)) as tar:
            tar.extractall(baseline, filter="data")
        for row in source_cases(disclosed):
            case = row["case"]
            request, read_pid, source = source_request(row, prior["cases"][case], identity["cases"][case])
            clean = {**request, "display": None, "self_appearance": None}
            base = run(baseline, clean)
            control = run(ROOT, clean)
            parent_only = run(ROOT, {**request, "self_appearance": None})
            full, repeated = (run(ROOT, request) for _ in range(2))
            require({k: v for k, v in base.items() if k != "pid"} == {k: v for k, v in control.items() if k != "pid"},
                    "the previously unqualified no-intent route changed bytes or ownership")
            proof = compare(control, parent_only, full, repeated, request)
            cases[case] = {**source, "generated": proof,
                           "feature_id_and_clock_mapping": source_owner_boundary(source, proof),
                           "guarded_request_sha256": sha256(canonical(request)).hexdigest(),
                           "delta_only": {"parent": sorted((TREE, VISUALS)), "child": [CMGR, VISUALS]}}
            processes.extend((read_pid, *(entry["pid"] for entry in (base, control, parent_only, full, repeated))))
            for role in ("parent", "child"):
                checked(Path(row[role]), row[role + "_sha256"])
        request = independently_authored()
        first, second = (run(ROOT, request) for _ in range(2))
        require({k: v for k, v in first.items() if k != "pid"} == {k: v for k, v in second.items() if k != "pid"}
                and [row[1] for row in first["parent_store"]["occurrence_rows_in_wire_order"]]
                == [row[0] for row in request["display"]["visibility"]][::-1],
                "unrelated geometry and renamed occurrence order were not independently generated")
        cases["unrelated"] = {key: value for key, value in first.items() if key != "pid"}
        processes.extend((first["pid"], second["pid"]))
        refusals = {fault: run(ROOT, refusal_request(request, fault), error)
                    for fault, error in FAULTS.items()}
    require(len(processes) == len(set(processes)), "guarded workers were not fresh processes")
    for generated in (False, True):
        a, b = ((cases[key]["generated"] if generated else cases[key])["parent_store"] for key in ("A20", "A21"))
        require(b["terminal_map"] - a["terminal_map"] == 6
                and Counter(b["compound_objects"]) - Counter(a["compound_objects"]) == COMPOUND,
                "the extra occurrence did not derive its exact six-entry map growth")
        require(b["bytes"] - a["bytes"] == 192 + 2 * (
            b["parent_header_locator_codepoints"] - a["parent_header_locator_codepoints"]),
            "parent store length did not follow the extra compound row and modeled UTF-16 locator")
    files = subprocess.check_output(("git", "diff", "--name-only", BASE), cwd=ROOT).decode().splitlines()
    files += subprocess.check_output(("git", "ls-files", "--others", "--exclude-standard", "--", "src", "re/tooling"),
                                     cwd=ROOT).decode().splitlines()
    return {"schema": "kit.sw2026.planar-visual-composition.v1", "base": BASE, "prior_identity_sha256": IDENTITY,
            "source_files": {name: file_sha(ROOT / name) for name in sorted(set(files)) if name.endswith(".py")},
            "cases": cases, "refusals": refusals, "guarded_fresh_successes": len(processes),
            "guarded_source_reads": 2, "guarded_writer_successes": len(processes) - 2,
            "legacy_radial_process_proof": radial_proof,
            "writer_runtime_reads": 0, "native_processes": 0, "new_heldout_credit": 0,
            "published_cad_files": 0, "whole_source_admitted": False, "public_write_qualified": False, "passed": True}


def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("build", "deliver", "prove"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--disclosed", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode in ("build", "deliver"):
        print(json.dumps(compose(args.root.resolve(strict=True), json.load(sys.stdin), args.mode == "deliver"),
                         sort_keys=True, allow_nan=False))
    else:
        require(args.disclosed is not None and args.output is not None, "disclosed input and unused private output are required")
        output, disclosed = args.output.resolve(), args.disclosed.resolve(strict=True)
        require(not output.exists() and not output.is_relative_to(ROOT) and not output.is_relative_to(disclosed),
                "use an unused output outside the worktree and disclosed source")
        print(write(output / "Receipt.json", prove(disclosed, output)))


if __name__ == "__main__":
    main()
