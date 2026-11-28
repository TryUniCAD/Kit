from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
import inspect
import json
from pathlib import Path
import sys

SW2026 = Path(__file__).resolve().parents[2]
REPO = SW2026.parents[2]
PARENT_HASH = "2267cb6bc7e02d05be19ce5105ba3e43240eb4d1ad897647237dc875445d0dc2"
CHILD_HASH = "92b83376b42ca55aa3b32a350635585c788ea0f968cc6e54f1730fdeb3c99caa"
SCHEMA = "kit.sw2026.concentric-occurrence-number-discriminator.v1"


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def write(path, value):
    with path.open("x") as target:
        json.dump(value, target, sort_keys=True, indent=2, allow_nan=False)
        target.write("\n")


def refuse(action):
    try:
        action()
    except ValueError as error:
        return str(error)
    return None


def project(args):
    from convert import open_document
    from convert.Geometry.Parasolid import NativeId
    from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.ReadOccName import (
        ReadOccName,
    )
    from convert.adapters.solidworks.Assembly.Assembly import DecodeNativeAsm
    from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import (
        ReadAsmModel,
    )
    from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylChild import (
        ReadCylChild,
    )
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import (
        IndexFeatures,
    )
    from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import (
        ReadNativeLink,
    )
    from FreshCylinderInput import make_document
    from interchange import (
        CadDocument,
        CadSource,
        Configuration,
        MateConstraint,
        MateEntity,
        MateGroup,
    )
    from interchange.assembly.ComponentDefinition import ComponentDef
    from interchange.assembly.ComponentInstance import ComponentInst
    from interchange.document.Models.DocumentModel import AssemblyData, ComponentDoc
    from interchange.serialization.EncodeData import ToData
    from para.concentric.ProjectConcentricRadialIntent import (
        light_values,
        radial_from_archive,
        source_scene,
    )

    parent_raw, child_raw = args.parent.read_bytes(), args.child.read_bytes()
    require(
        digest(parent_raw) == PARENT_HASH
        and digest(child_raw) == CHILD_HASH
        and args.parent.parent == args.child.parent,
        "actual disclosed D01 pair required",
    )
    document = open_document(
        args.parent, strict=True, include_brep=True, include_tessellation=False
    )
    graph = document.assembly
    require(
        document.source.sha256 == PARENT_HASH
        and document.metadata["solidworks.typed_mates_semantics"]["status"]
        == "admitted"
        and refuse(lambda: ReadAsmModel(document))
        == "assembly root contains unprojected model content",
        "expected the complete D01 read and unchanged whole-source refusal",
    )
    (entry,) = graph.documents
    source_child = entry.document
    (child_config,) = source_child.configurations
    (root_config,) = document.configurations
    require(
        source_child.source.sha256 == CHILD_HASH
        and child_config.active
        and root_config.active,
        "D01 definitions do not select the same actual active child",
    )
    child_owner = ReadCylChild(args.child, source_child, child_config.name)
    native_circle, radial = radial_from_archive(child_owner.LinkValue)
    source_boss = ReadExtrude(
        child_owner.LinkValue,
        child_owner.FeatureValue,
        IndexFeatures(child_owner.LinkValue),
    )
    require(
        source_boss.ModeValue == "blind" and not source_boss.IsReversed,
        "ordinary forward blind child required",
    )
    scene, lights = source_scene(child_owner.LinkValue)
    source_archive = SldprtArchive.from_bytes(parent_raw)
    native_parent = DecodeNativeAsm(source_archive)
    native_link = ReadNativeLink(source_archive, 0)
    (mate_group,) = (
        row
        for row in IndexFeatures(native_link).values()
        if row.ClassValue.NameValue == "moMateGroup_c"
    )

    root_id, child_id = "assembly/root", "assembly/child"
    (child_name,) = {item.name for item in native_parent.occurrences}
    require(
        child_name == args.child.stem,
        "ordinary source occurrence basename is not the actual child name",
    )
    portable_by_feature = {
        row.attributes["native_feature_id"]: row for row in graph.instances
    }
    rows = []
    instance_ids = {}
    for item in native_parent.occurrences:
        source = portable_by_feature[item.feature_id]
        require(
            ReadOccName(source.name) == (item.name, str(item.reference_number))
            and source.reference_number == str(item.reference_number)
            and source.order == item.order
            and source.configuration_name == child_config.name,
            "SDK occurrence number does not match the actual owned native reference",
        )
        instance_id = "instance/" + str(item.order)
        instance_ids[source.id] = instance_id
        rows.append(
            ComponentInst(
                instance_id,
                source.name,
                child_id,
                root_id,
                source.transform,
                order=source.order,
                reference_number=source.reference_number,
                configuration_name=source.configuration_name,
                configuration_id="config/default",
                suppressed=source.suppressed,
                hidden=source.hidden,
                fixed=source.fixed,
                flexible=source.flexible,
                exclude_from_bom=source.exclude_from_bom,
            )
        )
    require(
        len(rows) == len(graph.instances) == 2,
        "expected two actual D01 direct instances",
    )

    child = make_document(
        {
            "name": child_name,
            "axis": "z",
            "plane": "Front Plane",
            "driver": "radius",
            "reversed": False,
            "center_mm": native_circle.CenterValue,
            "radius_mm": radial.value_mm,
            "depth_mm": source_boss.RequireDepth().DepthValue.value_mm,
        }
    )
    require(
        child.configurations[0].name == child_config.name,
        "expected the discriminator's ordinary child configuration",
    )
    (rule,) = graph.mates
    owners = {row.id: row for row in graph.mate_entities}
    entities = []
    for order, identifier in enumerate(rule.entity_ids):
        entity = owners[identifier]
        (instance,) = entity.instance_path
        require(
            entity.source_entity_id
            == NativeId("face", child_owner.FaceValue.IndexValue + 1)
            and entity.radius == radial.value_mm,
            "source mate does not select the actual owned child cylinder",
        )
        entities.append(
            MateEntity(
                "selection/" + str(order),
                root_id,
                (instance_ids[instance],),
                "cylinder",
                child.bodies[0].id + "-sweep-side-1-face",
                radius=entity.radius,
            )
        )
    mate = MateConstraint(
        "mate/one",
        rule.name,
        "concentric",
        root_id,
        tuple(value.id for value in entities),
        alignment=rule.alignment,
        attributes={"rotation_locked": rule.attributes["rotation_locked"]},
    )
    root_name = args.parent.stem
    portable_graph = AssemblyData(
        root_id,
        (
            ComponentDef(
                root_id,
                root_name,
                "assembly",
                configuration_name=root_config.name,
                configuration_id="config/root",
            ),
            ComponentDef(
                child_id,
                child_name,
                "part",
                document_id="document/child",
                configuration_name=child_config.name,
                configuration_id=child.configurations[0].id,
                body_ids=(child.bodies[0].id,),
            ),
        ),
        tuple(rows),
        documents=(ComponentDoc("document/child", child),),
        mate_entities=tuple(entities),
        mates=(mate,),
        mate_groups=(
            MateGroup("group/one", ReadNodeName(mate_group), root_id, (mate.id,)),
        ),
    )
    fresh = CadDocument(
        CadSource(
            "kit-neutral", "<occurrence-number-discriminator>", child.source.sha256
        ),
        (Configuration("config/root", root_config.name, True),),
        (),
        (),
        (),
        (),
        (),
        (),
        metadata={"name": root_name},
        units=document.units,
        assembly=portable_graph,
    )
    fresh.AssertValid()
    args.output.mkdir()
    request = args.output / "Neutral.json"
    write(
        request,
        {
            "schema": SCHEMA,
            "document": ToData(fresh),
            "scene": scene,
            "lights": [light_values(value) for value in lights],
        },
    )
    write(
        args.output / "Projection.json",
        {
            "schema": SCHEMA,
            "request_sha256": digest(request.read_bytes()),
            "source_parent": PARENT_HASH,
            "source_child": CHILD_HASH,
            "source_folders_remain_unadmitted": True,
            "occurrences": [
                {
                    "name": row.name,
                    "number": row.reference_number,
                    "order": row.order,
                    "configuration": row.configuration_name,
                    "fixed": row.fixed,
                }
                for row in rows
            ],
            "native_processes_started": 0,
            "heldout_inputs_read": 0,
        },
    )


def build(args):
    from convert.adapters.solidworks.Assembly.Assembly import DecodeNativeAsm
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.AssemblyPreparation.Model.CheckAsmOcc import (
        CheckAsmOcc,
    )
    from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import (
        ReadAsmModel,
    )
    from interchange.serialization.Deserialize import FromData
    from para.concentric.PrepareRadialConcentric import guarded_bundle, read_intents

    source_file = Path(inspect.getfile(CheckAsmOcc)).resolve()
    require(
        source_file.is_relative_to(args.sdk_root.resolve() / "src"),
        "unexpected SDK root provided admission",
    )
    raw = args.request.read_bytes()
    require(digest(raw) == args.sha256, "neutral request identity changed")
    request = json.loads(raw)
    require(
        set(request) == {"schema", "document", "scene", "lights"}
        and request["schema"] == SCHEMA,
        "unexpected request fields",
    )
    document = FromData(request["document"])
    graph = document.assembly
    rows = graph.instances
    if args.variant == "omitted":
        rows = tuple(replace(row, reference_number="") for row in rows)
    elif args.variant == "mismatch":
        rows = (replace(rows[0], reference_number=rows[1].reference_number), rows[1])
    elif args.variant == "unknown":
        rows = (replace(rows[0], attributes={"unrepresented": True}), rows[1])
    elif args.variant == "noncanonical":
        rows = (
            replace(rows[0], reference_number="0" + rows[0].reference_number),
            rows[1],
        )
    document = replace(document, assembly=replace(graph, instances=rows))
    result = {
        "schema": SCHEMA,
        "revision": args.revision,
        "guard_source_sha256": digest(source_file.read_bytes()),
        "neutral_request_sha256": args.sha256,
        "variant": args.variant,
        "native_processes_started": 0,
        "heldout_inputs_read": 0,
        "refusal": refuse(lambda: ReadAsmModel(document)),
    }
    args.output.mkdir()
    if result["refusal"] is None:
        child = graph.documents[0].document
        files, proof = guarded_bundle(
            document,
            child,
            request["scene"],
            read_intents(request["lights"], args.written_at),
            args.destination,
            args.written_at,
        )
        native = DecodeNativeAsm(SldprtArchive.from_bytes(files["parent"]))
        result.update(
            generated_sha256={role: digest(data) for role, data in files.items()},
            xml_occurrences=[
                (f"{item.name}-{item.reference_number}", str(item.reference_number))
                for item in native.occurrences
            ],
            fixed_flags=proof["parent"]["fixed_flags"],
            runtime_io_attempts=proof["runtime_io_attempts"],
            repeated_builds=proof["builds"],
            linked_streams=8,
        )
        (args.output / f"{document.metadata['name']}.SLDASM").write_bytes(
            files["parent"]
        )
        (args.output / f"{child.metadata['name']}.SLDPRT").write_bytes(files["child"])
    write(args.output / "Result.json", result)


def main():
    parser = ArgumentParser(
        description="Discriminate authored occurrence numbers on disclosed D01"
    )
    parser.add_argument("--sdk-root", type=Path, default=REPO)
    commands = parser.add_subparsers(dest="command", required=True)
    source = commands.add_parser("project")
    for name in ("parent", "child", "output"):
        source.add_argument("--" + name, type=Path, required=True)
    emitter = commands.add_parser("build")
    for name in ("request", "output"):
        emitter.add_argument("--" + name, type=Path, required=True)
    for name in ("revision", "destination", "sha256"):
        emitter.add_argument("--" + name, required=True)
    emitter.add_argument("--written-at", type=int, required=True)
    emitter.add_argument(
        "--variant",
        choices=("explicit", "omitted", "mismatch", "unknown", "noncanonical"),
        required=True,
    )
    args = parser.parse_args()
    sys.path[:0] = [str(args.sdk_root / "src"), str(SW2026), str(SW2026 / "serial")]
    (project if args.command == "project" else build)(args)


if __name__ == "__main__":
    main()
