from argparse import ArgumentParser
from base64 import b64decode, b64encode
from dataclasses import replace
import json
from pathlib import Path, PureWindowsPath
import subprocess
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProveD01ConcentricBridge import (
    AUTHOR,
    FILES,
    LOCK,
    REPO,
    VISUAL,
    compare_root,
    fingerprint,
    model_request,
    proof_guard,
)
from AuditConcentricDisplayState import (
    INSTANCE,
    bind_visual,
    ctext,
    file_signature,
    model_inputs,
    xml_owner,
)
from CheckConcentricAssembly import verify_emission
from Classes import registry
from ProjectConcentricRadialIntent import read_intents
from ProjectD01Concentric import project_d01, require
from ProveConcentricSourceBrep import D01_LOCKED, checked, source_case
from VerifySdkVisualStore import inspect_store
from defs.Visual import load_visual_states

from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.AsmDisplayIn import (
    AsmDisplayIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.MakeAsmVisual import (
    MakeAsmVisual,
)
from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import (
    FeatureInstant,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.MakeCylAsm import (
    MakeCylAsm,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.NotesInput import (
    NotesInput,
)
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.Assembly import XmlRoot
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.AssemblyPreparation.Children.ReadAsmPlanes import (
    ReadAsmPlanes,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.PlanCylMate import (
    PlanCylMate,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.PrepCylChild import (
    PrepCylChild,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import (
    ReadAsmModel,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.ReadAsmPaths import (
    ReadAsmPaths,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Recipe.MakeAsmRecipe import (
    MakeAsmRecipe,
)
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.serialization.Deserialize import FromData

BASE = "0cd00727bac5068f3a21df07d6e3981b6cef3f69"
BRIDGE = "bfde612890cb5952042fe63b46a1d34fa17d5cd28e6d18aaa1b5a60125138de6"
DISPLAY_AUDIT = "6d2e2dcddbaf2db31696cd925e0d8e360947ee29db739a8b7a1cdb9c0c98c944"
EPOCH = 1816324000


def build_arguments(request, document, model):
    epoch = request["written_at"]
    paths = ReadAsmPaths(
        model.RootValue.name, model.ChildValue.name, request["destination"], epoch
    )
    child = PrepCylChild(
        model.ChildDocument,
        paths.ChildValue,
        request["child_scene"],
        read_intents(request["child_lights"], epoch),
    )
    plan = PlanCylMate(
        document, model.ChildDocument, child.CandidateValue, child.FaceTag
    )
    root = MakeAsmRecipe(
        model,
        MakePartRecipe(child.CandidateValue.PlanValue, epoch),
        ReadAsmPlanes(document),
        paths.ParentValue,
    )
    notes = NotesInput(
        *request["root_notes"], FeatureInstant(epoch, 5), FeatureInstant(epoch, 6)
    )
    system = replace(
        root.SystemValue,
        FolderNames=tuple(tuple(row) for row in request["root_folders"]),
        CabinetName=request["root_cabinet"],
        OriginName=request["root_origin"],
        LightValues=read_intents(request["root_lights"], epoch),
        NotesValue=notes,
        HasEmptyExplodedView=request["root_empty_exploded_view"],
    )
    root = replace(root, ModelName=request["root_model_name"], SystemValue=system)
    axes = tuple(tuple(row) for row in request["endpoint_local_axes"])
    return (
        plan.CandidateValue,
        root,
        plan.Placements,
        plan.EndIndexes,
        child.FaceTag,
        replace(plan.MateInput, LocalAxes=axes),
    )


def refuse(action, expected):
    try:
        action()
    except ValueError as error:
        require(expected in str(error), str(error))
        return str(error)
    raise ValueError("unqualified singleton assembly display was emitted")


def refusals(args, initial, state):
    one, two = state.VisibilityValues
    bad = {
        "hidden_singleton": (
            (replace(state, VisibilityValues=(one, (two[0], False))),),
            "one all-visible default",
        ),
        "renamed_default": (
            (replace(state, NameValue="Only"),),
            "one all-visible default",
        ),
        "unknown_occurrence": (
            (replace(state, VisibilityValues=(one, ("Alien-2", True))),),
            "each actual occurrence",
        ),
        "duplicate_occurrence": (
            (replace(state, VisibilityValues=(one, one)),),
            "each actual occurrence",
        ),
        "numeric_visibility": (
            (replace(state, VisibilityValues=(one, (two[0], 1))),),
            "explicit Boolean",
        ),
        "two_states": (
            (state, replace(state, NameValue="Extra")),
            "one default state or",
        ),
    }
    result = {
        label: refuse(lambda: MakeCylAsm(*args, DisplayValues=rows), expected)
        for label, (rows, expected) in bad.items()
    }
    header, top = initial.HeaderValue, initial.TopHeader
    file_owner = top.FieldsValue["f38"]
    detached = ArchiveNode(
        top.ClassValue,
        {
            **top.FieldsValue,
            "f38": ArchiveNode(file_owner.ClassValue, dict(file_owner.FieldsValue)),
        },
    )
    result["detached_header_file"] = refuse(
        lambda: MakeAsmVisual(
            initial.StateValue,
            initial.ChildValue,
            (header, detached),
            initial.OccurrenceValues,
            initial.MateValues,
            (state,),
        ),
        "both actual headers and their shared assembly self-file",
    )
    result["misordered_actual_owners"] = refuse(
        lambda: MakeAsmVisual(
            initial.StateValue,
            initial.ChildValue,
            (header, top),
            tuple(reversed(initial.OccurrenceValues)),
            initial.MateValues,
            (state,),
        ),
        "actual ordered direct occurrences",
    )
    return result


def file_identity(archive, requested_path, requested_name, reg):
    model_header = ReadHeaderGraph(
        archive.require("Contents/Config-0-ModelHeader"), 19000
    )
    top = ReadHeaderGraph(archive.require("Header2"), 19000)
    header, saved = (node.FieldsValue["f38"] for node in (model_header, top))
    main = ReadFileKey(header)
    require(
        main == ReadFileKey(saved) and main[:3] == (requested_name, requested_path, 3),
        "generated parent headers changed their own file identity",
    )
    expected_signature = file_signature(header.FieldsValue["shared"])
    visual, _ = load_visual_states(archive.require(VISUAL), reg)
    for row in visual.head["root"].f["comps"]:
        context = row["comp"].f
        (item,) = context["f20"].f["f08"].f["f08"]
        external = item["o"].f["f10"]
        detached = context["f40"].FieldsValue["shared"]
        require(
            file_signature(external) == file_signature(detached) == expected_signature
            and ctext(external["h10"]) == ctext(detached["h10"]) == requested_name
            and ctext(external["h18"]) == ctext(detached["h18"]) == requested_path,
            "display contexts disagree with the generated parent title locator or signature",
        )
    return {
        "title": requested_name,
        "locator_sha256": fingerprint(requested_path.encode()),
        "matching_parent_headers": 2,
        "context_count": len(visual.head["root"].f["comps"]),
    }


def worker(request):
    document = FromData(request["document"])
    model = ReadAsmModel(document)
    GetDocumentCaps(model.ChildDocument)
    reg = registry()
    guard = proof_guard()
    args = build_arguments(request, document, model)
    display = AsmDisplayIn(
        request["root_display_name"],
        tuple((row.name, not row.hidden) for row in model.Occurrences),
    )
    initial = MakeCylAsm(*args)
    parent = MakeCylAsm(*args, DisplayValues=(display,))
    require(
        parent.ChildValue is initial.ChildValue is args[0]
        and VISUAL not in initial.StreamsValue
        and parent.StreamsValue.keys() - initial.StreamsValue.keys() == {VISUAL}
        and all(parent.StreamsValue[k] == v for k, v in initial.StreamsValue.items()),
        "singleton changed the common parent streams or owned child",
    )
    measured = inspect_store(
        parent.BytesValue, ((display.NameValue, display.VisibilityValues),), reg
    )
    archive = SldprtArchive.from_bytes(parent.BytesValue)
    parent_identity = file_identity(
        archive, request["destination"], request["root_model_name"], reg
    )
    recipe = args[1]
    shifted = replace(
        recipe, SystemValue=replace(recipe.SystemValue, HasEmptyExplodedView=False)
    )
    shifted_parent = MakeCylAsm(args[0], shifted, *args[2:], DisplayValues=(display,))
    shifted_store = inspect_store(
        shifted_parent.BytesValue, ((display.NameValue, display.VisibilityValues),), reg
    )
    require(
        measured["xml_occurrences"] != shifted_store["xml_occurrences"]
        and [row[1:] for row in shifted_store["visual_occurrences"]]
        == [row[1:] for row in measured["visual_occurrences"]],
        "computed singleton did not follow independent occurrence allocation",
    )
    child = args[0]
    child_bridge = SimpleNamespace(
        candidate=child,
        atom_id=child.SystemValue.RootValue.FieldsValue["fd88"]["atoms"][0][
            "o"
        ].FieldsValue["f140"],
        projection=SimpleNamespace(lateral_face_tag=args[4]),
    )
    mate = verify_emission(
        parent.BytesValue,
        child_bridge,
        args[5].AlignmentCode,
        False,
        model.FixedIndex,
        tuple(model.Occurrences[index].name for index in args[3]),
        expected_local_axes=args[5].LocalAxes,
    )
    negative = refusals(args, initial, display)
    require(not guard, "singleton generation attempted external access")
    return {
        "parent": b64encode(parent.BytesValue).decode("ascii"),
        "prior_no_display_parent_sha256": fingerprint(initial.BytesValue),
        "child_sha256": fingerprint(child.BytesValue),
        "unchanged_parent_streams": len(initial.StreamsValue),
        "mate": mate,
        "store": measured,
        "parent_identity": parent_identity,
        "shifted_occurrence_ids": shifted_store["xml_occurrences"],
        "shifted_store_sha256": shifted_store["sha256"],
        "refusals": negative,
        "runtime_external_accesses": len(guard),
    }


def source_store(raw, expected):
    archive = SldprtArchive.from_bytes(raw)
    refs, config, name, planes, header = model_inputs(archive)
    index = xml_owner(XmlRoot(archive.require(INSTANCE)), refs, config, name, True)
    _, _, visual = bind_visual(
        archive.require(VISUAL),
        registry(),
        archive,
        config,
        index,
        refs,
        planes,
        header,
    )
    require(
        visual["sha256"] == expected["sha256"] and visual["byte_identity"],
        "locked native display store drifted",
    )
    return {
        "display_state_key": visual["state"]["id"],
        "state_name": visual["state"]["name"],
        "configuration": [config, name],
        "xml_members": index["state"]["members"],
        "xml_state_id": index["state"]["id"],
        "store_order": [
            row["feature_id"] for row in visual["components_in_store_order"]
        ],
        "store_sha256": visual["sha256"],
        "store_bytes": visual["bytes"],
    }


def run(disclosures):
    source = disclosures / "ConcentricMateSourcePacket02/Disclosed/D01"
    lock = json.loads(checked(source / "lock.json", LOCK))
    author = json.loads(checked(source / "author.json", AUTHOR))
    require(
        lock["source_locked"]
        and not lock["heldout_source_locked"]
        and author["passed"]
        and author["result"]["passed"],
        "native source custody changed",
    )
    reports = REPO / "re/solidworks/measurements/2026"
    bridge = json.loads(checked(reports / "ConcentricD01DesignBridge01.json", BRIDGE))
    prior = json.loads(
        checked(reports / "ConcentricDisplayState01.json", DISPLAY_AUDIT)
    )
    result = {}
    for phase, hashes in D01_LOCKED.items():
        require(
            tuple(
                lock["native_artifacts"][phase.lower()][role]["sha256"]
                for role in ("parent", "child")
            )
            == hashes,
            "source is outside the disclosed custody lock",
        )
        folder = source / "Native" / phase
        parent, raw, shape = source_case(folder, *FILES, hashes)
        root_refusal = refuse(
            lambda: ReadAsmModel(parent),
            "assembly root contains unprojected model content",
        )
        before = source_store(raw, prior["cases"]["D01" + phase]["visual"])
        projected = project_d01(parent, raw, shape)
        destination = str(
            PureWindowsPath(r"C:\KitD01ConcentricBridge") / phase / FILES[0]
        )
        request = json.dumps(
            model_request(projected, EPOCH, destination),
            sort_keys=True,
            allow_nan=False,
        ).encode()
        historic = bridge["cases"][phase]
        require(
            fingerprint(request) == historic["neutral_constructor_request_sha256"],
            "neutral D01 request drifted",
        )
        command = (sys.executable, "-I", "-B", str(HERE), "--worker")
        first, second = (
            subprocess.run(command, input=request, capture_output=True, timeout=120)
            for _ in range(2)
        )
        require(
            first.returncode == second.returncode == 0
            and first.stdout == second.stdout,
            (first.stderr + second.stderr).decode(),
        )
        generated = json.loads(first.stdout)
        serialized = b64decode(generated.pop("parent"), validate=True)
        stock = historic["comparison_candidate"]
        require(
            generated["prior_no_display_parent_sha256"] == stock["parent_sha256"]
            and generated["child_sha256"] == stock["parts_sha256"],
            "original no-display assembly or child changed",
        )
        compare_root(projected, serialized, generated)
        store = generated["store"]
        require(
            store["states"] == [[before["display_state_key"], before["state_name"]]]
            and store["configuration"] == before["configuration"]
            and all(row[2] == [1] for row in store["visual_occurrences"]),
            "computed singleton disagrees with the strict original state semantics",
        )
        for file, expected in zip(FILES, hashes, strict=True):
            checked(folder / file, expected)
        result[phase] = {
            "source_parent_sha256": hashes[0],
            "source_child_sha256": hashes[1],
            "request_sha256": fingerprint(request),
            "source_visual": before,
            "whole_source_refusal": root_refusal,
            "generated_parent_sha256": fingerprint(serialized),
            "generated_parent_bytes": len(serialized),
            **generated,
        }
    return {
        "schema": "kit.sw2026.disclosed-d01-parent-display.v1",
        "sdk_base": BASE,
        "source_build": "34.5.2.0604",
        "source_lock_sha256": LOCK,
        "prior_design_bridge_sha256": BRIDGE,
        "prior_display_audit_sha256": DISPLAY_AUDIT,
        "guarded_workers": 4,
        "runtime_cad_launches": 0,
        "new_heldout_credit": 0,
        "public_writer_qualified": False,
        "complete_appearance_parity": False,
        "cases": result,
    }


def main():
    parser = ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--worker", action="store_true")
    mode.add_argument("--disclosures", type=Path)
    args = parser.parse_args()
    result = worker(json.load(sys.stdin)) if args.worker else run(args.disclosures)
    print(
        json.dumps(
            result,
            sort_keys=True,
            indent=2 if not args.worker else None,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
