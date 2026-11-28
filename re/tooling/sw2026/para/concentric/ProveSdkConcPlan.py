import argparse
import codecs
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from json import dumps, loads
from math import isclose
from pathlib import Path, PureWindowsPath
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
TOOLS = HERE.parents[2]
sys.path[:0] = [str(ROOT / "src"), str(TOOLS), str(TOOLS / "serial"), str(HERE.parent)]

from PrepareConcentricPersistence import derive_session
from convert.Geometry.Extrude.Circular.CircularExtrude import BuildCircular
from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.MakeCylAsm import MakeCylAsm
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.PlanCylMate import PlanCylMate
from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.ReadAsmPaths import ReadAsmPaths
from convert.adapters.solidworks.Core.AssemblyPreparation.PlanAsmWrite import PlanAsmWrite
from convert.adapters.solidworks.Core.AssemblyPreparation.Recipe.MakeAsmRecipe import MakeAsmRecipe
from convert.adapters.solidworks.Core.Preparation.Circle.PrepareCircle import PrepareCircle
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.assembly.AssemblyEnums import MateAlignment
from interchange.document.Models.DocumentModel import CadDocument
from interchange.serialization.Deserialize import FromData
from para.concentric.ConcentricAssembly import principal_planes
from para.cylinder.CylinderAttachment import attach_cylinder_mut


FEATURE = "e5e005dc738ad379f0485accc78d7f72002cccdc1b14186ea43ed82e4f444fe3"
BETA = "c18bd23e516c36029794ea20b73f1ba6946a04fc6375bd7ebc82e08046078c06"
BREP = "2b00d988374d26b39d6edfd2752fe488d7ad9a527a3d1913bdd384ee614fbf63"
EPOCH = 1795303000


def load_doc(path, expected):
    raw = path.read_bytes()
    assert sha256(raw).hexdigest() == expected
    result = FromData(loads(raw))
    result.assert_valid()
    return result


def replace_mate(document, **changes):
    graph = document.assembly
    return replace(document, assembly=replace(graph, mates=(replace(graph.mates[0], **changes),)))


def embed_child(document, child):
    graph = document.assembly
    return replace(document, assembly=replace(graph, documents=(replace(graph.documents[0], document=child),)))


def radial_contrast(document):
    child = document.assembly.documents[0].document
    (sketch,) = child.sketches
    (radial_id,) = sketch.parameter_ids
    radius = sketch.entities[0].geometry.radius
    parameters = tuple(replace(row, value=replace(row.value, value=radius)) if row.id == radial_id else row
                       for row in child.parameters)
    relations = tuple(replace(row, kind="radius") if row.parameter_id == radial_id else row
                      for row in sketch.constraints)
    updated = replace(child, sketches=(replace(sketch, constraints=relations),), parameters=parameters)
    return embed_child(document, updated)


def preload(document):
    for source in (document, document.assembly.documents[0].document):
        GetDocumentCaps(source)
        source.assert_valid()
    for encoding in ("utf-8", "utf-16-le", "utf-16-be", "cp1252", "ascii"):
        codecs.lookup(encoding)
    for suffix in ("DocumentComponentValidate", "DocumentGraphValidate",
                   "DocumentMateEntityValidate", "DocumentMateGroupValidate", "DocumentMateValidate",
                   "DocumentMeshValidate"):
        import_module("interchange.document.Validation." + suffix)


def attach(document):
    graph = document.assembly
    child = graph.documents[0].document
    target = str(PureWindowsPath(r"C:\KitConcAdmissionCase") / (document.metadata["name"] + ".SLDASM"))
    paths = ReadAsmPaths(document.metadata["name"], child.metadata["name"], target, EPOCH)
    options = WriteOptions(values={"final_destination": paths.ChildValue.PathName})
    part = PrepareCircle(child, BytesIO(), EPOCH, options, Measured=True)
    session, updates = derive_session(child, EPOCH)
    mode = "diameter" if part.PlanValue.IsDiameter else "radius"
    attachment = attach_cylinder_mut(part, session, updates, 0, tessellated_faces=True, driver_mode=mode)
    return attachment, paths


def check_archive(parent, plan, fixed):
    assert parent.ChildValue is plan.CandidateValue
    assert tuple(bool(row.FieldsValue["f408"] & 1) for row in parent.OccurrenceValues) == fixed
    (mate,) = parent.MateValues
    fields = mate.FieldsValue
    assert fields["f3b4"] == plan.MateInput.AlignmentCode
    assert fields["f4b8"] == int(plan.MateInput.RotationLocked)
    for slot, (item, end) in enumerate(zip(fields["f410"], plan.EndsValue, strict=True)):
        wrapper = item["o"].FieldsValue
        component = wrapper["f58"].FieldsValue
        chain = component["f58"].FieldsValue["f20"].FieldsValue["f08"].FieldsValue["f08"]
        (external,) = chain
        assert external["o"].FieldsValue["f50"] is parent.OccurrenceValues[end.IndexValue]
        assert wrapper["f7c"] == slot
        assert component["fe8"].FieldsValue["f70"] == plan.FaceValue.FaceTag
        assert wrapper["f100"] == plan.FaceValue.RadiusValue
    assert SldprtArchive.from_bytes(parent.BytesValue).streams == parent.StreamsValue


def check_plan(document, attachment, paths):
    graph = document.assembly
    child = graph.documents[0].document
    candidate = attachment.candidate
    face_tag = attachment.projection.lateral_face_tag
    plan = PlanCylMate(document, child, candidate, face_tag)
    ordered = tuple(sorted(graph.instances, key=lambda row: row.order))
    entities = {row.id: row for row in graph.mate_entities}
    (mate,) = graph.mates
    selected = tuple(entities[key] for key in mate.entity_ids)
    fixed = tuple(row.fixed for row in ordered)
    assert plan.ModelValue.GraphValue is graph and plan.ModelValue.ChildDocument is child
    assert plan.CandidateValue is candidate and plan.MateValue is mate
    assert all(end.EntityValue is expected for end, expected in zip(plan.EndsValue, selected, strict=True))
    assert tuple(end.OccurrenceValue.id for end in plan.EndsValue) == tuple(row.instance_path[0] for row in selected)
    assert all(end.OccurrenceValue is ordered[index] for end, index in zip(plan.EndsValue, plan.EndIndexes, strict=True))
    assert plan.MateInput.FixedIndex == plan.EndIndexes.index(fixed.index(True))
    assert plan.ModelValue.FixedIndex == fixed.index(True)
    assert plan.MateInput.RotationLocked is mate.attributes["rotation_locked"]
    assert plan.MateInput.AlignmentCode == (1 if str(mate.alignment) == "aligned" else 2)
    assert plan.FaceValue.FaceTag == face_tag
    assert plan.FaceValue.FaceNodeId == attachment.lateral_face_node_id
    assert plan.FaceValue.BodyAtom == attachment.atom_id
    assert all(end.source_entity_id == plan.NeutralFace.id for end in selected)
    circle = child.sketches[0].entities[0].geometry
    assert isclose(plan.FaceValue.RadiusValue, circle.radius / 1000, rel_tol=1e-12)
    for end in plan.EndsValue:
        matrix = end.OccurrenceValue.transform
        expected = matrix.TransformPoint((circle.center.x, circle.center.y, 0.0))
        assert all(isclose(a, b / 1000, rel_tol=1e-12, abs_tol=1e-12)
                   for a, b in zip(end.OriginValue, expected, strict=True))
        assert all(isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
                   for a, b in zip(end.AxisValue, (matrix.values[2], matrix.values[6], matrix.values[10]), strict=True))
    part_recipe = MakePartRecipe(plan.CandidateValue.PlanValue, EPOCH)
    recipe = MakeAsmRecipe(plan.ModelValue, part_recipe, principal_planes(document, EPOCH), paths.ParentValue)
    parent = MakeCylAsm(candidate, recipe, plan.Placements, plan.EndIndexes, face_tag, plan.MateInput)
    check_archive(parent, plan, fixed)
    return {
        "assembly_sha256": sha256(parent.BytesValue).hexdigest(),
        "child_sha256": sha256(candidate.BytesValue).hexdigest(),
        "body_atom": plan.FaceValue.BodyAtom, "face_node": plan.FaceValue.FaceNodeId,
        "neutral_side": plan.NeutralFace.id, "alignment": plan.MateInput.AlignmentCode,
        "rotation_locked": plan.MateInput.RotationLocked,
        "fixed_occurrence_slot": fixed.index(True), "fixed_selected_slot": plan.MateInput.FixedIndex,
        "actual_occurrence_order": [row.id for row in ordered], "selected_indexes": plan.EndIndexes,
        "world_centers_m": tuple(end.OriginValue for end in plan.EndsValue),
        "world_axes": tuple(end.AxisValue for end in plan.EndsValue),
        "radius_m": plan.FaceValue.RadiusValue,
        "driver_mode": "diameter" if candidate.PlanValue.IsDiameter else "radius",
        "authored_parent_datum_count": len(document.support_planes),
    }


def refused(call, diagnostic):
    try:
        call()
    except (ValueError, TypeError) as error:
        assert diagnostic in str(error), (diagnostic, str(error))
        return diagnostic
    raise AssertionError("unqualified concentric assembly reached a plan")


def check_negatives(document, attached, brep_fixture):
    graph = document.assembly
    child = graph.documents[0].document
    candidate, tag = attached.candidate, attached.projection.lateral_face_tag

    def endpoint(**changes):
        ends = (replace(graph.mate_entities[0], **changes), graph.mate_entities[1])
        return replace(document, assembly=replace(graph, mate_entities=ends))

    def plan(doc=document, part=child, face=tag):
        return PlanCylMate(doc, part, candidate, face)

    def placement(matrix):
        first, second = graph.instances
        moved = replace(second, transform=replace(second.transform, values=tuple(matrix)))
        return replace(document, assembly=replace(graph, instances=(first, moved)))

    alternate = brep_fixture.assembly.documents[0].document
    spec = candidate.PlanValue
    circle = child.sketches[0].entities[0].geometry
    equivalent = BuildCircular(spec.BodyId, child.support_planes[0].transform, circle,
                               0., spec.DepthValue * 1000., circle.radius, circle.radius)[0]
    same_with_brep = replace(child, brep=equivalent)
    noncoaxial = list(graph.instances[1].transform.values)
    noncoaxial[3] += 5.317
    reflected = list(graph.instances[1].transform.values)
    for index in (0, 4, 8):
        reflected[index] = -reflected[index]
    results = {
        "missing_face": refused(lambda: plan(endpoint(source_entity_id="foreign/absent")), "actual neutral lateral face"),
        "cap_face": refused(lambda: plan(endpoint(source_entity_id=spec.BodyId + "-sweep-side-0-face")), "actual neutral lateral face"),
        "native_index": refused(lambda: plan(endpoint(source_entity_id="parasolid:face:101")), "actual neutral lateral face"),
        "radius_metres": refused(lambda: plan(endpoint(radius=circle.radius / 1000.)), "radius differs"),
        "boolean_radius": refused(lambda: plan(endpoint(radius=True)), "radius differs"),
        "same_occurrence": refused(lambda: plan(endpoint(instance_path=graph.mate_entities[1].instance_path)), "two distinct occurrences"),
        "bad_lock": refused(lambda: plan(replace_mate(document, attributes={"rotation_locked": 1})), "explicit boolean"),
        "bad_alignment": refused(lambda: plan(replace_mate(document, alignment=MateAlignment.KAntiAligned)), "coaxial alignment"),
        "off_axis_pose": refused(lambda: plan(placement(noncoaxial)), "coaxial alignment"),
        "reflected_pose": refused(lambda: plan(placement(reflected)), "proper rigid placement"),
        "wrong_face_tag": refused(lambda: plan(face=tag + 1), "minted kernel owner"),
        "cloned_neutral_child": refused(lambda: plan(part=replace(child)), "actual embedded child"),
        "supplied_disclosed_brep": refused(lambda: plan(brep_fixture, alternate), "feature-only child"),
        "supplied_equal_brep": refused(lambda: plan(embed_child(document, same_with_brep), same_with_brep), "feature-only child"),
    }
    assert alternate.brep is not None and same_with_brep.brep is equivalent
    header = candidate.HeaderValue.FieldsValue
    original = header["f40"]
    try:
        header["f40"] = original + 1
        results["stale_generated_owner"] = refused(plan, "typed links disagree with its generated archive")
    finally:
        header["f40"] = original
    return results


def prove(document, brep_fixture, name):
    preload(document)
    active = False
    attempts = []

    def guard(event, args):
        if active and (event in {"open", "os.listdir", "os.scandir", "os.system", "os.fork", "os.posix_spawn"}
                       or event.startswith(("socket.", "subprocess.", "ctypes.", "winreg."))
                       or (event == "import" and args[0].split(".")[0] in ("pythoncom", "win32com", "FreeCAD", "adsk"))):
            attempts.append(event)
            raise RuntimeError("guarded concentric planning attempted runtime access: " + event)

    sys.addaudithook(guard)
    restored = CadDocument.from_json(document.to_json(indent=None))
    active = True
    try:
        assert restored == document
        attachment, paths = attach(document)
        initial = check_plan(document, attachment, paths)
        repeated, replay_paths = attach(restored)
        replay = check_plan(restored, repeated, replay_paths)
        assert initial == replay
        verified = {"authored": initial, "neutral_json": replay}
        negatives = {}
        if name == "feature":
            mate = document.assembly.mates[0]
            reversed_selection = replace_mate(document, entity_ids=tuple(reversed(mate.entity_ids)))
            variant = check_plan(reversed_selection, attachment, paths)
            assert variant["selected_indexes"] == (1, 0) and variant["fixed_selected_slot"] == 1
            verified["reordered_endpoints"] = variant
            negatives = check_negatives(document, attachment, brep_fixture)
            negatives["public_plan"] = refused(lambda: PlanAsmWrite(document, paths.ParentValue.PathName, EPOCH),
                                               "all three actual principal plane ids")
    finally:
        active = False
    assert not attempts
    return {"case": name, "verified": verified, "refusals": negatives, "runtime_io_attempts": len(attempts)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=("feature", "beta", "radius"), required=True)
    parser.add_argument("--beta-document", type=Path)
    args = parser.parse_args()
    fixtures = ROOT / "re/solidworks/inputs"
    if args.case == "beta":
        if args.beta_document is None:
            parser.error("--case beta requires the pinned --beta-document")
        document = load_doc(args.beta_document, BETA)
    else:
        document = load_doc(fixtures / "ConcentricFeatureNeutral01.json", FEATURE)
        if args.case == "radius":
            document = radial_contrast(document)
    brep_fixture = load_doc(fixtures / "ConcentricBrepNeutral01.json", BREP)
    print(dumps(prove(document, brep_fixture, args.case), allow_nan=False, sort_keys=True))
