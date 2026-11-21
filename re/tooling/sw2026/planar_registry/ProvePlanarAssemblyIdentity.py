from argparse import ArgumentParser
from codecs import lookup
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
from PlanarRegistryBuild import ROOT, artifact, bind, file_sha, load, require, write


BASE = "b18caa86c15d2c65ad95c9a572bbc9d06701da8c"
ROOT_PROOF = "c26b016604972bdcd0e7614d013e6600ace17654b5ba44499d33b1cb9e5f9c19"
PRIOR = "fb68f130ad521ca7473c6f3f239a71a276ccb2318c75586b1eb63de930965f55"
SEAL = "solidworks_source_semantic_sha256"
VISUAL_REFUSAL = "assembly visibility requires the ordinary radial child without a visual store"


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def source_hash(value):
    return sha256(canonical(value)).hexdigest()


def bind_sdk(root):
    bind(ROOT)
    sys.path.insert(0, str(root / "src"))
    for name in ("convert", "interchange"):
        module = import_module(name)
        require(Path(module.__file__).resolve().is_relative_to(root / "src"),
                "the worker imported a different SDK snapshot")


def excluded_modules():
    return [name for name in sys.modules if name in {"Swapp", "pythoncom", "pywintypes"} or name.startswith("win32com")]


def read_worker(root, request):
    bind_sdk(root)
    from convert import open_document
    from ProvePlanarMateGroup import checked, guarding

    parent, child = (Path(request[role]).resolve(strict=True) for role in ("parent", "child"))
    checked(parent, request["parent_sha256"])
    checked(child, request["child_sha256"])
    reads, _, denied = guarding(root, {parent, child})
    document = open_document(parent, include_brep=False, include_tessellation=False, strict=True)
    document.assert_valid()
    require(document.source.sha256 == request["parent_sha256"] and len(document.assembly.documents) == 1
            and document.assembly.documents[0].document.source.sha256 == request["child_sha256"]
            and reads == {parent.name, child.name} and not denied and not excluded_modules(),
            "the strict read did not use only the exact owned source pair")
    return {"pid": os.getpid(), "document": json.loads(document.to_json(indent=None))}


def compose(root, request):
    bind_sdk(root)
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    sys.addaudithook(audit.InspectEvent)

    def guard_network(event, args):
        if event.startswith(("socket.", "ctypes.")):
            audit.DeniedReads.append(event)
            raise PermissionError("assembly composition attempted a network or CAD runtime operation")

    sys.addaudithook(guard_network)
    from convert.adapters.solidworks.Archive.Construction.Assembly.EmitAsmStreams import EmitAsmStreams
    from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.MakePlanarGroup import MakePlanarGroup
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.AssemblyPreparation.PlanAsmWrite import PlanAsmWrite
    from interchange.serialization.Deserialize import FromData
    from CheckOriginalPlanarMethod import no_recorded_state
    from PlanarAssemblyIdentity import VISUALS, observe, xml_display
    from PlanarRootProjection import prepare_system
    from ProvePlanarRootProjection import observe_archive
    from ProveSketchLabelIntent import audit_link
    from SketchLabelIntent import make_group

    require(set(request) == {"document", "labels", "native_parent", "event", "parent_system", "model_name", "display"},
            "neutral composition requires explicit supported model and display inputs")
    no_recorded_state(request)
    document = FromData(request["document"])
    require(not any(key.startswith("kit.research_") for key in document.metadata),
            "a research source status cannot qualify native output")
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
    for encoding in ("utf-16-le", "utf-8", "utf-8-sig", "latin-1", "ascii"):
        lookup(encoding)
    document.assert_valid()
    audit.BeginBuild()
    path, event = request["native_parent"], request["event"]
    child = make_group(document, path, event, request["labels"]).ChildValue
    plan = PlanAsmWrite(document, path, event)
    recipe = replace(plan.RootRecipe, SystemValue=prepare_system(plan.RootRecipe.SystemValue, request["parent_system"], event))
    if request["model_name"] is not None:
        recipe = replace(recipe, ModelName=request["model_name"])
    bundle = MakePlanarGroup(child, recipe, plan.Occurrences, plan.MatesValue, plan.FixedIndex)
    require(bundle.ChildValue is child and VISUALS not in bundle.StreamsValue and VISUALS not in child.StreamsValue,
            "the internal identity experiment emitted an unexpected appearance owner")
    archive = SldprtArchive.from_bytes(bundle.BytesValue)
    identity = observe(archive, stem=document.metadata["name"], destination=path)
    expected = tuple(row.name for row in document.assembly.mates)
    measured = observe_archive(bundle, expected, True)
    comparison = audit_link(bundle)
    display = request["display"]
    extra = {}
    if display is not None:
        xml, intent = xml_display(bundle, display)
        observed = observe(archive, stem=document.metadata["name"], destination=path, tree_bytes=xml)
        require(observed["view"] is not None, "generated visibility XML did not bind to its actual binary owner")
        try:
            EmitAsmStreams(bundle.StateValue, child, recipe, (bundle.HeaderValue, bundle.TopHeader),
                           bundle.OccurrenceValues, bundle.MateValues, DisplayValues=(intent,))
        except ValueError as error:
            require(str(error) == VISUAL_REFUSAL, "the requested display store reached a different guard")
        else:
            raise ValueError("the unsupported whole display requested a native output")
        extra = {"xml": observed["view"], "xml_sha256": sha256(xml).hexdigest(),
                 "visual_guard": VISUAL_REFUSAL, "child_constructor_plan": type(child.PlanValue).__name__}
    require(not audit.DeniedReads and not excluded_modules(), "construction crossed the guarded neutral boundary")
    return {"pid": os.getpid(), "input_reads": len(audit.DeniedReads), "identity": identity,
            "occurrences": measured["occurrences"], "ordered_mates": measured["ordered_mates"],
            "parent": artifact(bundle), "child": artifact(child), "labels": comparison["actual"], **extra}


def dispatch(command, root, payload, *, error=None):
    response = subprocess.run((sys.executable, "-I", "-B", str(TOOL), command, "--root", str(root)),
                              input=canonical(payload), capture_output=True, check=False, timeout=120)
    if error is not None:
        require(response.returncode != 0 and not response.stdout and error in response.stderr.decode()
                and b"PermissionError" not in response.stderr, "the negative request refused at an unrelated guard")
        return error
    require(response.returncode == 0, response.stderr.decode(errors="replace"))
    return json.loads(response.stdout)


def display_delta(first, second, source_case):
    old = first["assembly"]["attributes"]
    new = second["assembly"]["attributes"]
    if "typed_display_states" in old:
        require(source_case == "A20" and first == second, "the existing two-member strict read changed")
        return []
    require(source_case == "A21" and "typed_display_states" in new,
            "the third actual occurrence was not admitted")
    a, b = (json.loads(canonical(value)) for value in (first, second))
    b["assembly"]["attributes"].pop("typed_display_states")
    require(a["metadata"].pop(SEAL) != b["metadata"].pop(SEAL) and a == b,
            "the three-member read changed an unrelated source owner")
    return ["assembly.attributes.typed_display_states", "metadata." + SEAL]


def source_mutations(archive):
    from convert.adapters.solidworks.Assembly.Display.CheckDisplay import CheckDisplay
    from convert.adapters.solidworks.Assembly.Display.ReadDisplayXml import KDisplayNs, ReadDisplayXml
    from convert.adapters.solidworks.Container.Format import KComponentTreeStream
    from convert.adapters.solidworks.Core.Native import ParseXml
    from ProvePlanarSourceLabels import refusal

    data = archive.require(KComponentTreeStream)
    tree = ParseXml(data)
    row, = tree.findall("sw:swConfigurationList/sw:swConfiguration", KDisplayNs)
    row.set("swReference", "Foreign model")
    alias = refusal(CheckDisplay, (archive, ReadDisplayXml(tree)), "assembly display state refers to a foreign binary model")
    tree = ParseXml(data)
    state, = tree.findall(".//sw:swDisplayState", KDisplayNs)
    value = state.attrib["swShowState"]
    state.set("swShowState", value[:-4] + "No,")
    mixed = refusal(ReadDisplayXml, (tree,), "assembly display state cannot bind the measured ordered visibility")
    return {"foreign_alias": alias, "mixed_visibility": mixed}


def compare_builds(old, control, first, second, request):
    require(all(row["input_reads"] == 0 for row in (old, control, first, second)),
            "a composition depended on runtime data")
    def stable(row):
        return {name: value for name, value in row.items() if name != "pid"}

    require(stable(old) == stable(control), "the no-intent bundle changed at the same explicit input")
    require(stable(first) == stable(second), "independent identity builds differ")
    require(first["child"] == control["child"] and first["labels"] == control["labels"]
            and first["occurrences"] == control["occurrences"] and first["ordered_mates"] == control["ordered_mates"],
            "splitting document identities altered child presentation or linked assembly semantics")
    actual = first["identity"]
    require(actual["native_model"] == actual["configuration_reference"] == request["model_name"]
            and actual["file_stem"] == control["identity"]["file_stem"]
            and actual["configuration"] == control["identity"]["configuration"]
            and actual["view"] is None and first["xml"]["StateName"] == request["display"]["name"]
            and [(row["NativeName"], row["Visible"]) for row in first["xml"]["MemberValues"]]
                == [tuple(row) for row in request["display"]["visibility"]],
            "native identity or independent XML projection differs")
    streams = first["parent"]["streams"]
    baseline = control["parent"]["streams"]
    require(set(streams) == set(baseline), "a model-name request unexpectedly emitted another logical owner")
    return sorted(name for name, value in streams.items() if value != baseline[name])


def evidence(disclosed, output):
    bind_sdk(ROOT)
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.AssemblyWriting.CheckAsmShape import CheckAsmShape
    from interchange import CadDocument
    from PlanarAssemblyIdentity import observe, request_view, source_visuals
    from PlanarPriorAdmission import source_intent
    from PlanarRootProjection import project
    from PlanarSourceLabels import project_labels
    from ProvePlanarMateGroup import checked, source_cases
    from ProvePlanarSourceLabels import reconstruct, refusal
    from ProveSketchLabelIntent import payload

    measures = ROOT / "re/solidworks/measurements/2026"
    root_proof = load(measures / "SdkPlanarRootSourceProjection01.json", ROOT_PROOF)
    prior = load(measures / "SdkPlanarPriorSourceAdmission01.json", PRIOR)
    require(root_proof["passed"] and not root_proof["whole_source_admission"], "prior root proof has a different scope")
    output.mkdir()
    cases, processes = {}, []
    with TemporaryDirectory(prefix="KitPlanarIdentityBaseline") as folder:
        baseline = Path(folder).resolve()
        frozen = subprocess.check_output(("git", "archive", BASE, "src"), cwd=ROOT)
        with open_tar(fileobj=BytesIO(frozen)) as archive:
            archive.extractall(baseline, filter="data")
        for row in source_cases(disclosed):
            slot = row["case"]
            parent, child = (Path(row[role]) for role in ("parent", "child"))
            author = json.loads(checked(parent.parent / "Record.json", row["native_record_sha256"]))
            parent_raw, child_raw = (checked(path, row[role + "_sha256"])
                                     for role, path in (("parent", parent), ("child", child)))
            original, fresh = (dispatch("read", root, row) for root in (baseline, ROOT))
            sdk_delta = display_delta(original["document"], fresh["document"], slot)
            source_json = canonical(fresh["document"]).decode()
            source = CadDocument.from_json(source_json)
            neutral, previous = source_intent(source, author["job"]["case"], child_raw)
            labels, _ = project_labels(source.assembly.documents[0].document, child_raw, neutral.assembly.documents[0].document,
                                       prior["cases"][slot]["exact_source_display"])
            system, audit = project(source, neutral, parent_raw, previous["source_intent"]["assembly"]["system"])
            require(audit["root_owner_counts"] == root_proof["cases"][slot]["source_member_counts"],
                    "identified root presentation differs from the prior measured owners")
            native_assembly = SldprtArchive.from_bytes(parent_raw)
            source_roles = observe(native_assembly, stem=parent.stem)
            display = request_view(source, source_roles)
            request = {**payload(neutral, labels), "parent_system": system,
                       "model_name": source_roles["native_model"], "display": display}
            require(all(row[key].encode() not in canonical(request) for key in ("parent_sha256", "child_sha256")),
                    "a frozen source identity entered the semantic writer request")
            case_dir = output / slot
            case_dir.mkdir()
            custody = reconstruct(source, source_json, neutral, case_dir)
            write(case_dir / "NeutralRequest.json", request)
            default = {**request, "model_name": None, "display": None}
            old, control = (dispatch("build", root, default) for root in (baseline, ROOT))
            first, second = (dispatch("build", ROOT, request) for _ in range(2))
            changed = compare_builds(old, control, first, second, request)
            source_guard = refusal(CheckAsmShape, (source,), "assembly root contains unprojected model content")
            broken = {**request, "model_name": ""}
            empty_name = dispatch("build", ROOT, broken, error="assembly model name must not be empty")
            crossed = {**request, "display": {**display, "visibility": list(reversed(display["visibility"]))}}
            bad_order = dispatch("build", ROOT, crossed, error="source display intent must own the actual generated occurrences in order")
            cases[slot] = {
                "source_locks": {key: row[key] for key in ("parent_sha256", "child_sha256", "native_record_sha256")},
                "source_read_delta": sdk_delta, "source": source_roles, "generated": first["identity"],
                "independently_bound_generated_xml": first["xml"], "constructed_xml_sha256": first["xml_sha256"],
                "source_visual_owners": source_visuals(native_assembly, SldprtArchive.from_bytes(child_raw)),
                "child_constructor_plan": first["child_constructor_plan"],
                "visual_guard": first["visual_guard"], "whole_source_guard": source_guard,
                "refusals": {**source_mutations(native_assembly), "blank_model_name": empty_name, "crossed_display_order": bad_order},
                "stable_previous_bytes": True, "unchanged_child_bytes": True, "constructed_parent": first["parent"]["sha256"],
                "previous_parent": control["parent"]["sha256"], "child_sha256": first["child"]["sha256"],
                "changed_parent_streams": changed, "neutral_request_sha256": source_hash(request),
                "exact_original_wire_custody": {key: custody[key] for key in ("source_wire_sha256", "source_child_wire_sha256",
                    "complete_source_wire_restored_exactly", "complete_source_child_wire_restored_exactly")},
            }
            processes.extend(item["pid"] for item in (original, fresh, old, control, first, second))
            checked(parent, row["parent_sha256"])
            checked(child, row["child_sha256"])
    require(len(set(processes)) == len(processes), "required guarded workers were not fresh processes")
    files = (
        TOOL, TOOL.with_name("PlanarAssemblyIdentity.py"), TOOL.with_name("PlanarRootProjection.py"),
        ROOT / "re/tooling/sw2026/para/concentric/MakeDisplayTree.py",
        *(ROOT / "src/convert/adapters/solidworks" / name for name in (
            "Archive/Construction/Assembly/AssemblyInput.py", "Archive/Construction/Assembly/CheckAsmMeta.py",
            "Archive/Construction/Assembly/MakeAsmBase.py", "Assembly/Display/ReadDisplayXml.py")),
    )
    return {"schema": "kit.sw2026.planar-assembly-identity.v1", "base_revision": BASE,
            "prior_root_receipt_sha256": ROOT_PROOF, "source_files": {str(path.relative_to(ROOT)): file_sha(path) for path in files},
            "cases": cases, "successful_workers": len(processes), "guarded_writer_refusals": 2 * len(cases),
            "runtime_input_reads": 0, "native_processes": 0, "published_cad_files": 0,
            "additional_heldout_credit": 0, "whole_source_admitted": False, "passed": True}


def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("read", "build", "prove"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--disclosed", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode == "prove":
        require(args.disclosed is not None and args.output is not None, "disclosed base and private output are required")
        output = args.output.resolve()
        disclosed = args.disclosed.resolve(strict=True)
        require(not output.exists() and not output.is_relative_to(ROOT) and not output.is_relative_to(disclosed),
                "use an unused private output outside the worktree and source packet")
        print(write(output / "Receipt.json", evidence(disclosed, output)))
    else:
        operation = read_worker if args.mode == "read" else compose
        print(json.dumps(operation(args.root.resolve(strict=True), json.load(sys.stdin)), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
