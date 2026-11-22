from argparse import ArgumentParser
from dataclasses import asdict, replace
from io import BytesIO
from math import isclose
import codecs
import json
from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ProveSdkCylParent import CASES, create, disclosed, finger, parent
from CheckConcentricAssembly import verify_emission
from ConcentricNeutralAdmission import bind_cylinder, project_concentric
from ProjectConcentricRadialIntent import read_intents
from ProveSignedConcentricWriter import emit_parts
from convert import open_document
from convert.api.ApiContext import GetRegistry
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import FeatureInstant
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.ReadMintedCyl import ReadMintedCyl
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CheckCylWire import CheckCylWire
from convert.adapters.solidworks.Archive.Construction.Part.MakeCirclePart import MakeCirclePart
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectCircle import ProjectCircle
from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import LightInput
from convert.adapters.solidworks.Archive.Partition.History.ReadXmtStages import ReadXmtStages
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Container.Parasolid import DecodePartition
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.PrepCylChild import PrepCylChild
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.ReadAsmPaths import ReadAsmPaths
from convert.adapters.solidworks.Core.AssemblyPreparation.Placements.ReadAsmPlace import ReadAsmPlace
from convert.adapters.solidworks.Core.AssemblyPreparation.Recipe.MakeAsmRecipe import MakeAsmRecipe
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadLightInput import ReadLightInput
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylNodes import ReadCylNodes
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadOutputAtom import ReadOutputAtom
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import ReadChildren
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from para.concentric.ConcentricAssembly import principal_planes


SCENE = "Lights and Cameras"


def lights_for(case, raw, epoch):
    if case != "persistence":
        return read_intents(raw, epoch)
    assert raw["feature_target"] == {"DateCode": 2026306, "ParasolidVersion": 370108}
    return (
        LightInput(
            KindValue="ambient", **raw["ambient"], KeepInScene=True, EnabledInPv=False,
            UseCartesian=True, PvBrightness=1., PvShadows=True, PvQuality=16.,
            DirectionValue=None, ShadowSoftness=None, CreatedValue=FeatureInstant(epoch, 0),
        ),
    )


def view(bundle):
    keys = ("child", "parent")
    values = bundle.ChildValue.BytesValue, bundle.BytesValue
    return dict(zip(keys, values, strict=True))


def compose(document, model, paths, child, axes, display):
    part = child.CandidateValue
    nodes = ReadCylNodes(SldprtArchive.from_bytes(part.BytesValue))
    profile = "diameter" if part.PlanValue.IsDiameter else "radius"
    binding = bind_cylinder(model.ChildDocument, part, nodes, profile="derived_feature", driver_mode=profile)
    intent = project_concentric(document, {model.ChildValue.id: binding})
    epoch = paths.ParentValue.SavedAt
    recipe = MakePartRecipe(part.PlanValue, epoch)
    metadata = MakeAsmRecipe(model, recipe, principal_planes(document, epoch), paths.ParentValue)
    places = tuple(ReadAsmPlace(row) for row in model.Occurrences)
    bridge = SimpleNamespace(candidate=part, atom_id=binding.child.AtomValue,
                             projection=SimpleNamespace(lateral_face_tag=child.FaceTag))
    return parent((bridge, intent, metadata, places), axes, display), (bridge, intent, metadata, places)


def drivers(document):
    parameters = {parameter.id: parameter for parameter in document.parameters}
    radial, = document.sketches[0].parameter_ids
    depth, = document.feature_timeline[0].parameter_ids
    assert radial != depth and set(parameters) == {radial, depth}
    return parameters[radial], parameters[depth]


def public_part(raw, plan, document):
    options = {"source_format": "solidworks.sldprt", "strict": True}
    full = open_document(BytesIO(raw), include_brep=True, **options)
    design = open_document(BytesIO(raw), include_brep=False, **options)
    assert len(full.bodies) == len(design.bodies) == 1
    assert full.bodies[0].name == document.bodies[0].name
    assert full.brep is not None and design.brep is None
    brep = full.brep
    topology = tuple(len(getattr(brep, name)) for name in ("bodies", "faces", "edges", "vertices"))
    assert topology == (1, 3, 2, 2)
    authored, actual = drivers(document), full.parameters
    assert len(authored) == len(actual) == len(design.parameters) == 2
    assert full.parameters == design.parameters and actual[0].owner_id != actual[1].owner_id
    sketch, = full.sketches
    profile, = [feature for feature in full.feature_timeline if feature.id == actual[0].owner_id]
    assert profile.name == plan.SketchName and profile.sketch_id == sketch.id
    assert profile.parameter_ids == sketch.parameter_ids == (actual[0].id,)
    boss, = [feature for feature in full.feature_timeline if feature.id == actual[1].owner_id]
    assert boss.name == plan.FeatureName and boss.sketch_id == sketch.id
    assert boss.parameter_ids == (actual[1].id,)
    assert full.bodies[0].final_feature_id == design.bodies[0].final_feature_id == boss.id
    for expected, measured in zip(authored, actual, strict=True):
        assert expected.name == measured.name == "D1" and expected.value.unit == measured.value.unit == "mm"
        assert isclose(expected.value.value, measured.value.value, rel_tol=1e-12)
    assert isclose(sketch.entities[0].geometry.radius, plan.CircleValue.RadiusValue * 1000, rel_tol=1e-12)
    return {"topology": topology, "live_d1_owner_ids": [row.owner_id for row in actual],
            "live_d1_mm": [row.value.value for row in actual], "strict_modes": 2,
            "full_body_name": full.bodies[0].name, "design_only_body_name": design.bodies[0].name}


def check_child(child, document, scene, lights):
    part = child.CandidateValue
    physical = ReadMintedCyl(part, child.FaceTag)
    raw = part.BytesValue
    archive = SldprtArchive.from_bytes(raw)
    nodes = ReadCylNodes(archive)
    frames = DecodePartition(archive.require(KPartitionStream), KPartitionStream)
    link = ReadNativeLink(archive, 0)
    model = link.ConfigValue.RootValue.FieldsValue
    feature, = [node for node in link.ResolvedValue.RootsValue if node.ClassValue.NameValue == "moExtrusion_c"]
    atom = ReadOutputAtom(feature)
    visibility, = model["ffe0"]
    manager_entry, = model["fd88"]["atoms"]
    assert visibility["k"] is atom and visibility["v"] == 0 and manager_entry["o"] is atom
    assert atom.FieldsValue["f140"] == physical.BodyAtom
    assert atom.FieldsValue["f180"] == atom.FieldsValue["f1b0"] == 1
    assert link.ConfigValue.HeaderValue.FieldsValue["f40"] == part.CurrentConfig.FieldsValue["f860"]
    selectors = (model["fe38"].FieldsValue["f18"], feature.FieldsValue["f3d0"].FieldsValue["f18"])
    stages = ReadXmtStages(frames[1].data, nodes, selectors)
    active, activation, initial = stages
    assert (active.MarkValue.Integer("id"), activation.MarkValue.Integer("id"), initial.MarkValue.Integer("id")) == (4, 2, 1)
    assert active.NodesValue[1].Integer("body") != 0
    assert activation.NodesValue[1].Integer("body") == initial.NodesValue[1].Integer("body") == 0
    assert active.UndoValue is not None and activation.UndoValue is not None
    assert len(active.UndoValue.RemovedValue) == 53 and not activation.UndoValue.RemovedValue
    assert active.MarkValue.Integer("n_new_nodes") - len(active.UndoValue.RemovedValue) == 11
    folder = model["f1e0"]
    assert folder.FieldsValue["f18"].FieldsValue["f08"] == scene
    assert tuple(ReadLightInput(row) for row in ReadChildren(folder)) == lights
    return {
        "child_owner": asdict(physical), "scene_count": len(lights), "retained_marks": [4, 2, 1],
        "active_nodes": len(nodes), "physical_removals": len(active.UndoValue.RemovedValue),
        "hidden_pointer_allocations": 11, "linked_streams": 5,
        "typed_public_read": public_part(raw, part.PlanValue, document),
    }


def older_control(document, output, measured_child):
    plan = ProjectCircle(document)
    recipe = BindPartIntent(document, plan, MakePartRecipe(plan, output.SavedAt), output)
    baseline = MakeCirclePart(document, recipe)
    CheckCylWire(baseline)
    assert "Contents/Config-0-Partition" not in baseline.StreamsValue
    expected = {
        "Contents/Config-0", "Contents/Config-0-ResolvedFeatures", "Contents/Config-0-ModelHeader",
        "Header2", "Contents/CMgr", "Contents/CMgrHdr2", KPartitionStream,
    }
    actual = {
        key for key in set(measured_child.StreamsValue) | set(baseline.StreamsValue)
        if baseline.StreamsValue.get(key) != measured_child.StreamsValue.get(key)
    }
    assert actual == expected
    return {"plain_sha256": finger(baseline.BytesValue), "changed_streams": sorted(actual)}


def varied_part(document, output, lights):
    sketch, = document.sketches
    entity, = sketch.entities
    feature, = document.feature_timeline
    radial, depth = drivers(document)
    radial = replace(radial, value=replace(radial.value, value=radial.value.value + 0.314))
    depth = replace(depth, value=replace(depth.value, value=depth.value.value + 1.117))
    scale = 2 if ProjectCircle(document).IsDiameter else 1
    entity = replace(entity, geometry=replace(entity.geometry, radius=radial.value.value / scale))
    sketch = replace(sketch, entities=(entity,))
    feature = replace(feature, definition=replace(feature.definition, length=depth.value))
    changes = {row.id: row for row in (radial, depth)}
    parameters = tuple(changes[row.id] for row in document.parameters)
    variant = replace(document, sketches=(sketch,), feature_timeline=(feature,), parameters=parameters)
    scene = SCENE + " from the independent neutral edit"
    result = PrepCylChild(variant, output, scene, lights)
    record = check_child(result, variant, scene, lights)
    return result, record


def refused(case, document, output, lights, candidate):
    feature, = document.feature_timeline
    radial, depth = drivers(document)
    reversed_doc = replace(document, feature_timeline=(
        replace(feature, definition=replace(feature.definition, reversed=True)),
    ))
    foreign_radial = replace(document, parameters=(replace(radial, value=replace(radial.value, value=radial.value.value + 0.01)), depth))
    wrong_epoch = (
        replace(lights[0], CreatedValue=FeatureInstant(output.SavedAt - 1, 0)), *lights[1:],
    )
    wrong_name = (replace(lights[0], NameValue=feature.name), *lights[1:])
    tests = {
        "wrong_support_or_direction": (lambda: PrepCylChild(reversed_doc, output, SCENE, lights), "support driver or end profile"),
        "foreign_driver_value": (lambda: PrepCylChild(foreign_radial, output, SCENE, lights), "radial driving length disagrees"),
        "empty_scene": (lambda: PrepCylChild(document, output, SCENE, ()), "ambient or ordered four-light scene"),
        "stale_light_epoch": (lambda: PrepCylChild(document, output, SCENE, wrong_epoch), "light times"),
        "crossed_light_owner": (lambda: PrepCylChild(document, output, SCENE, wrong_name), "unique owned scene names"),
        "unrepresented_source_metadata": (
            lambda: PrepCylChild(replace(document, metadata=dict(document.metadata) | {"unmapped": 1}), output, SCENE, lights),
            "unprojected document metadata",
        ),
        "wrong_output_kind": (
            lambda: PrepCylChild(document, replace(output, PathName=output.PathName[:-6] + "SLDASM"), SCENE, lights),
            "native self path extension differs",
        ),
        "crossed_side_tag": (lambda: ReadMintedCyl(candidate.CandidateValue, candidate.FaceTag + 1), "differs from its minted kernel owner"),
    }
    if case != "persistence":
        tests["reversed_scene_order"] = (
            lambda: PrepCylChild(document, output, SCENE, tuple(reversed(lights))), "ambient or ordered four-light scene"
        )
    result = {}
    for name, (call, expected) in tests.items():
        try:
            call()
        except ValueError as error:
            assert expected in str(error), (name, str(error))
            result[name] = str(error)
        else:
            raise ValueError("unqualified cylinder emitted: " + name)
    return result


def proof(case, inputs, references):
    document, axes, raw_lights, locator, epoch, display = inputs
    model = ReadAsmModel(document)
    paths = ReadAsmPaths(model.RootValue.name, model.ChildValue.name, locator, epoch)
    lights = lights_for(case, raw_lights, epoch)
    GetDocumentCaps(model.ChildDocument)
    GetRegistry()
    for encoding in ("utf-8", "utf-16-le", "utf-16-be", "cp1252", "ascii"):
        codecs.lookup(encoding)
    active = True
    attempted = []

    def audit(event, args):
        if active and (
            event in ("open", "os.listdir", "os.scandir", "os.system", "os.fork", "os.posix_spawn")
            or event.startswith(("socket.", "subprocess.", "ctypes.", "winreg."))
            or (event == "import" and args[0].split(".")[0] in ("pythoncom", "win32com", "FreeCAD", "adsk"))
        ):
            attempted.append(event)
            raise RuntimeError("cylinder generation attempted runtime access: " + event)

    sys.addaudithook(audit)
    try:
        if case == "locked":
            assert model.ChildDocument.brep is not None
            try:
                PrepCylChild(model.ChildDocument, paths.ChildValue, SCENE, lights)
            except ValueError as error:
                assert "native boundary payloads" in str(error)
                return {"authored_brep_refused": str(error), "writer_input_reads": 0, "native_launches": 0,
                        "protected_reads": 0, "generated": 0}
            raise ValueError("an unqualified supplied boundary payload was silently dropped")
        candidate = PrepCylChild(model.ChildDocument, paths.ChildValue, SCENE, lights)
        combined, bundle = compose(document, model, paths, candidate, axes, display)
        duplicate = PrepCylChild(model.ChildDocument, paths.ChildValue, SCENE, lights)
        other, _ = compose(document, model, paths, duplicate, axes, display)
        files = view(combined)
        assert files == view(other) and combined.ChildValue is candidate.CandidateValue
        if references:
            assert files == references
        else:
            previous = create(case, inputs)
            assert files == {"child": previous[0].candidate.BytesValue, "parent": emit_parts(previous, axes)}
        part_info = check_child(candidate, model.ChildDocument, SCENE, lights)
        changed, variant = varied_part(model.ChildDocument, paths.ChildValue, lights)
        assert changed.CandidateValue.BytesValue != files["child"]
        assert changed.CandidateValue.StreamsValue[KPartitionStream] != candidate.CandidateValue.StreamsValue[KPartitionStream]
        assert len(changed.CandidateValue.StreamsValue["Contents/Config-0"]) != len(
            candidate.CandidateValue.StreamsValue["Contents/Config-0"]
        )
        bridge, intent, _, _ = bundle
        mate_info = verify_emission(
            files["parent"], bridge, intent.alignment_code, intent.rotation_locked, intent.fixed_index,
            tuple(row.occurrence.name for row in intent.ends), expected_local_axes=axes,
        )
        negatives = refused(case, model.ChildDocument, paths.ChildValue, lights, candidate)
        control = older_control(model.ChildDocument, paths.ChildValue, candidate.CandidateValue)
    finally:
        active = False
    assert not attempted
    return {
        "files": {role: {"bytes": len(value), "sha256": finger(value),
                         "streams": len(SldprtArchive.from_bytes(value).streams)}
                  for role, value in files.items()},
        "native_exact_pair": bool(references), "explicit_alternate_epoch": None if references else epoch,
        "repeat_pairs": 2, "part_readback": part_info, "mate_readback": mate_info,
        "variation": {"bytes": len(changed.CandidateValue.BytesValue),
                      "sha256": finger(changed.CandidateValue.BytesValue),
                      "config_bytes": len(changed.CandidateValue.StreamsValue["Contents/Config-0"]),
                      "readback": variant},
        "ordinary_circle_control": control, "refusals": negatives,
        "writer_input_reads": 0, "native_launches": 0, "protected_reads": 0,
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--case", required=True, choices=tuple(CASES))
    parser.add_argument("--disclosures", type=Path, required=True)
    args = parser.parse_args()
    operands, references, trial_pin, native_pin = disclosed(args.disclosures, args.case)
    print(json.dumps({"case": args.case, "trial_sha256": trial_pin, "native_receipt_sha256": native_pin,
                      **proof(args.case, operands, references)}, sort_keys=True))


if __name__ == "__main__":
    main()
