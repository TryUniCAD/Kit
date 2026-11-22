from argparse import ArgumentParser
import codecs
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path, PureWindowsPath
import sys

HERE = Path(__file__).resolve()
REPO = HERE.parents[5]
TOOLS = HERE.parents[2]
sys.path[:0] = [str(REPO / "src"), str(TOOLS), str(TOOLS / "serial"), str(HERE.parent)]

from ConcentricNativeContract import checked, require
from ConcentricNeutralAdmission import bind_cylinder, project_concentric
from PrepareConcentricPersistence import derive_session
from PrepareGeneratedConcentric import windows_path
from PrepareSignedConcentricNative import model_with_lights
from ProjectConcentricRadialIntent import read_intents
from ProveSignedConcentricWriter import emit_parts, verify_parts
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.AsmDisplayIn import AsmDisplayIn
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylMateIn import CylMateIn
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.MakeCylAsm import MakeCylAsm
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.ReadAsmPaths import ReadAsmPaths
from convert.adapters.solidworks.Core.AssemblyPreparation.Placements.ReadAsmPlace import ReadAsmPlace
from convert.adapters.solidworks.Core.AssemblyPreparation.Recipe.MakeAsmRecipe import MakeAsmRecipe
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from interchange.serialization.Deserialize import FromData
from para.EmitAttachedPart import emit_attached_part
from para.concentric.ConcentricAssembly import principal_planes
from para.cylinder.CylinderAttachment import attach_cylinder_mut
from para.prism.SdkPrismAttachment import install_light

CASES = {
    "persistence": ("ConcentricPersistence01", "9b7e52d198a7e2a70902b3794fff1987451bc6a599ca1d557493eddc75a580c9"),
    "store": ("RadialConcentricDisplay04", "ac2696da314b7e2d4939fd75664270acecfe0274a479eafb9c2c6d5440aaed4b"),
    "aligned": ("SignedWrapperDiscovery02/Aligned", "8e0feb327fdacd559f9a9a56bcbb24ecf679bb4a40e9bff29f23f3cf7b03ae45"),
    "locked": ("SignedWrapperDiscovery02/AntiLocked", "3ba299ea8e9413aaf82dc3313e5cf8f570ac89f3b50ceb0079a574f5a158d199"),
}
NATIVE = {
    "persistence": ("ConcentricPersistenceNative01.json", "b95d6e806fdb7f167a46cd3ebbbfbf669a0bd1ac7696ec6287ba72b01376d785"),
    "store": ("ConcentricRadialDisplayStoresNative01.json", "d128bf6b61c69b3525743c596ee2d20a02f7b5d4b41c4d28ab088c0bc8300009"),
    "signed": ("ConcentricSignedWrapperNative01.json", "b37b7b0f38f268bbe7542bd99fa4c2e131a6a9cff8e60ea597e48e133702d2c6"),
}
ALTERNATE_EPOCH = 1795303000


def finger(raw):
    return sha256(raw).hexdigest()


def load(path, sha):
    return json.loads(checked(path, sha).read_bytes())


def disclosed(root, name):
    subdir, pin = CASES[name]
    folder = root / subdir
    trial = load(folder / "Trial.json", pin)
    native_role = name if name in ("persistence", "store") else "signed"
    receipt, sha = NATIVE[native_role]
    native = load(REPO / "re/solidworks/measurements/2026" / receipt, sha)
    if name == "persistence":
        require(native["passed"] and native["controls_healthy"]
                and native["distinct_native_processes"] == 4 and native["numeric_checks"] == 140
                and native["packet_sha256"] == pin
                and native["generated_input_sha256"] == trial["generated_sha256"],
                "disclosed persistence receipt differs")
    elif name == "store":
        native = native["cases"]["store-only"]
        require(native["variant_passed"] and native["controls_healthy"]
                and native["native_processes"] == 5 and native["candidate_numeric_checks"] == 84
                and native["trial_sha256"] == pin
                and native["generated_sha256"] == trial["generated_sha256"],
                "disclosed store-only receipt differs")
    else:
        native_case = native["cases"][Path(subdir).name]
        require(native["controls_healthy"] and native["fresh_native_processes"] == 8
                and native_case["complete_native_lifecycle"]
                and native_case["trial_sha256"] == pin
                and native_case["native_candidate_checks"] == 140
                and native_case["live_signed_axis_checks"] == 20
                and native_case["generated_sha256"] == trial["generated_sha256"],
                "disclosed signed receipt differs")
    require(trial["heldout_inputs_read"] == 0, "only independently disclosed inputs are permitted")
    def evidence(key):
        relative = "Evidence/" + key + ".json"
        return load(folder / relative, trial["files_sha256"][relative])
    raw = evidence("Neutral")
    destination = windows_path(folder / "Working" / trial["working_names"]["parent"])
    if name == "persistence":
        inputs = (FromData(raw), None, evidence("Ambient"), destination, evidence("Build")["written_at"], None)
    elif name == "store":
        build = evidence("Build")
        require(destination == build["same_final_links"]["parent"]["file_key"][1],
                "disclosed encoded parent path differs")
        document = FromData(raw["document"])
        names = tuple(row.name for row in document.assembly.instances)
        display = tuple(AsmDisplayIn(label, tuple(zip(names, map(bool, flags), strict=True)))
                        for label, flags in trial["authored_states"])
        inputs = (document, None, raw["lighting"], destination, build["authored_epoch"], display)
    else:
        axes = tuple(tuple(axis) for axis in raw["local_axes"])
        destination = str(PureWindowsPath(r"C:\KitSharedConcentricDiscriminator") / trial["working_names"]["parent"])
        inputs = (FromData(raw["document"]), axes, raw["lights"], destination, ALTERNATE_EPOCH, None)
    references = {}
    if name in ("persistence", "store"):
        references = {role: checked(folder / "Frozen" / basename, trial["generated_sha256"][role]).read_bytes()
                      for role, basename in trial["working_names"].items()}
    return inputs, references, pin, sha


def with_ambient(document, destination, epoch, ambient):
    model = ReadAsmModel(document)
    paths = ReadAsmPaths(model.RootValue.name, model.ChildValue.name, destination, epoch)
    child = model.ChildDocument
    options = WriteOptions(values={"final_destination": paths.ChildValue.PathName})
    prepared = PrepareNative(child, BytesIO(), epoch, options)
    session, updates = derive_session(child, epoch)
    attachment = attach_cylinder_mut(prepared, session, updates, 0, tessellated_faces=True)
    install_light(attachment.candidate, ambient, session.update_second)
    attached = emit_attached_part(attachment.candidate)
    attachment = replace(attachment, candidate=attached)
    nodes = {node.index: XmtNode(node.index, node.kind, node.fields) for node in attachment.projection.partition.nodes}
    binding = bind_cylinder(child, attached, nodes, profile="derived_feature")
    intent = project_concentric(document, {model.ChildValue.id: binding})
    recipe = MakePartRecipe(attached.PlanValue, epoch)
    metadata = MakeAsmRecipe(model, recipe, principal_planes(document, epoch), paths.ParentValue)
    placements = tuple(ReadAsmPlace(row) for row in model.Occurrences)
    return attachment, intent, metadata, placements


def create(name, requested):
    document, axes, light_rows, locator, epoch, _ = requested
    if name == "persistence":
        return with_ambient(document, locator, epoch, light_rows)
    return model_with_lights(document, "Lights and Cameras", read_intents(light_rows, epoch), locator, epoch)[0]


def parent(bundle, axes, display, *, mutation=None):
    attachment, intent, metadata, placements = bundle
    selected = tuple(end.occurrence_index for end in intent.ends)
    tag = attachment.projection.lateral_face_tag
    mate = CylMateIn(intent.mate.name, intent.alignment_code, intent.rotation_locked,
                   selected.index(intent.fixed_index), axes)
    if mutation == "repeated_selection":
        selected = (selected[0], selected[0])
    elif mutation == "crossed_tag":
        tag += 1
    elif mutation == "unproved_tag_high_word":
        tag += 1 << 16
    elif mutation == "wrong_axis":
        mate = replace(mate, LocalAxes=((1., 0., 0.),) * 2)
    elif mutation == "wrong_alignment":
        mate = replace(mate, AlignmentCode=3 - mate.AlignmentCode)
    elif mutation == "off_axis_pose":
        second = placements[1]
        x, y, z = second.FrameValue.OriginValue
        placements = (placements[0], replace(second, FrameValue=replace(second.FrameValue, OriginValue=(x + 0.001, y, z))))
    return MakeCylAsm(attachment.candidate, metadata, placements, selected, tag, mate, DisplayValues=display)


def reproduce(name, inputs, references):
    document, axes, _, _, _, display = inputs
    GetDocumentCaps(ReadAsmModel(document).ChildDocument)
    for encoding in ("utf-8", "utf-16-le", "utf-16-be", "cp1252", "ascii"):
        codecs.lookup(encoding)
    attempted = []
    active = True
    def guard(event, args):
        if not active:
            return
        if (event in ("open", "os.listdir", "os.scandir", "os.system", "os.fork", "os.posix_spawn")
                or event.startswith(("socket.", "subprocess.", "ctypes.", "winreg."))
                or (event == "import" and args[0].split(".")[0] in ("pythoncom", "win32com", "FreeCAD", "adsk"))):
            attempted.append(event)
            raise RuntimeError("concentric preparation attempted external access: " + event)
    sys.addaudithook(guard)
    try:
        bundle = create(name, inputs)
        result = parent(bundle, axes, display)
        repeated = parent(create(name, inputs), axes, display)
        files = {"parent": result.BytesValue, "child": result.ChildValue.BytesValue}
        require(result.ChildValue is bundle[0].candidate
                and files == {"parent": repeated.BytesValue, "child": repeated.ChildValue.BytesValue},
                "fresh independent model builds or actual child identity differ")
        require(files == references if references else result.BytesValue == emit_parts(bundle, axes),
                "the production graph differs from its exact independent comparator")
        fields = verify_parts(result.BytesValue, bundle, axes)
        negative = {
            "repeated_selection": "distinct ordered direct occurrences",
            "crossed_tag": "differs from its minted kernel owner",
            "unproved_tag_high_word": "differs from its minted kernel owner",
            "wrong_axis": "unit direction on the actual carrier",
            "wrong_alignment": "do not satisfy the selected alignment",
            "off_axis_pose": "do not satisfy the selected alignment",
            "stale_archive_stamp": "typed links disagree with its generated archive",
        }
        for label, needed in negative.items():
            header = bundle[0].candidate.HeaderValue.FieldsValue
            old_stamp = header["f40"]
            if label == "stale_archive_stamp":
                header["f40"] = old_stamp + 1
            try:
                parent(bundle, axes, display, mutation=label)
            except ValueError as error:
                require(needed in str(error), "unexpected refusal " + label + ": " + str(error))
            else:
                raise ValueError("unsupported concentric parent emitted: " + label)
            finally:
                header["f40"] = old_stamp
    finally:
        active = False
    require(not attempted, "external runtime attempts were recorded")
    return {
        "files": {role: {"bytes": len(value), "sha256": finger(value),
                         "streams": len(SldprtArchive.from_bytes(value).streams)} for role, value in files.items()},
        "native_exact_pair": bool(references), "signed_reference_parity_at_alternate_epoch": not references,
        "owner_readback": fields, "repeat_pairs": 2, "refusals": sorted(negative),
        "writer_input_reads": 0, "native_launches": 0, "heldout_reads": 0,
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--case", required=True, choices=tuple(CASES))
    parser.add_argument("--disclosures", type=Path, required=True)
    args = parser.parse_args()
    operands, references, trial_pin, native_pin = disclosed(args.disclosures, args.case)
    proof = reproduce(args.case, operands, references)
    print(json.dumps({"case": args.case, "trial_sha256": trial_pin,
                      "native_receipt_sha256": native_pin, **proof}, sort_keys=True))


if __name__ == "__main__":
    main()
