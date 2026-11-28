from argparse import ArgumentParser
from codecs import lookup
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
from struct import unpack
import sys

from BuildLocalBodyKernel import CASES, prism_model, require_neutral_prism
from LocalBodyEnvelope import LOCAL, PARTITION, decode
from LocalBodyKernel import BODY, _render_local, decode_local, fingerprint
from ReplayImportedBaseBody import require
from builders.EmptyPartition import PMARK_KIND, PARTITION_KIND, WORLD_KIND
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Header.MakeRootLog import MakeRootLog
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import KeywordConfig
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import KeywordFeature
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeywords import MakeKeywords
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import PartTextInput
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartArchive import EmitPartArchive
from convert.adapters.solidworks.Archive.Construction.Part.Imports.BindImportMut import BindImportMut
from convert.adapters.solidworks.Archive.Construction.Part.Imports.FinishImportMut import FinishImportMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import MakePartHeaders
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import MakePartDef
from convert.adapters.solidworks.Archive.Partition.ImportHistory.ImportEvent import ImportEvent
from convert.adapters.solidworks.Archive.Partition.ImportHistory.MakeImportHist import MakeImportHist
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeLocalPrism import MakeLocalPrism
from convert.adapters.solidworks.Archive.Partition.LocalWrite.EncodeLocalBody import EncodeLocalBody
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from downstream.lighting.AmbientInput import AmbientInput
from downstream.lighting.AttachAmbientMut import AttachAmbientMut
from interchange import CadDocument
from interchange.brep.Validation.BrepValidate import GetBrepErrors
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource
from interchange.serialization.EncodeData import ToData
from para.Partition import History, Node, Partition, Rollback, SCHEMAS, frame_payloads, read_partition, write_payloads
from para.rectangle.Allocate import DeltaEvent, MarkEvent, Session, allocate_marks, index_fields
from para.rectangle.AttributeChains import Install, attach_attributes
from para.rectangle.Attributes import RECTANGLE_DEFINITION_BY_NAME
from para.rectangle.Geometry import topology_nodes
from para.rectangle.RectanglePartition import complete_topology
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit


FEATURE_CLASS = "moBaseBody_c"
EPOCH = 1790000000
MODES = ("Bare", "Owned")
AUTHORED_AMBIENT = AmbientInput("Import ambient", "KitImportAmbient", 0.5, 0.5, 0.0, 0x00FFFFFF)
DEFAULT_FEATURE_NAME = "Imported geometry"


@dataclass(frozen=True)
class ImportedLabels:
    NameValue: str
    ConfigName: str
    FeatureName: str
    PlaneName: str = "Front Plane"
    AxisValue: str = "z"
    SketchName: str = ""


@dataclass(frozen=True, slots=True)
class ImportedPartSemantics:
    feature_name: str
    body_name: str
    body_name_is_authored: bool
    configuration_name: str
    properties: PartTextInput


def import_labels(name, configuration, feature_name, semantics):
    if semantics is None:
        return ImportedLabels(name, configuration.name, feature_name), feature_name, None
    require(type(semantics) is ImportedPartSemantics and feature_name == DEFAULT_FEATURE_NAME,
            "supply a separate local import semantic input without a competing feature label")
    require(configuration.name == semantics.configuration_name,
            "local import text belongs to the selected neutral configuration")
    require(type(semantics.body_name_is_authored) is bool
            and all(type(label) is str and label.strip() and label.isprintable()
                    for label in (semantics.configuration_name, semantics.feature_name, semantics.body_name)),
            "local import semantics require ordinary printable labels")
    require(not semantics.body_name_is_authored,
            "local import authored body name needs a qualified compatibility carrier")
    require(semantics.body_name == semantics.feature_name,
            "the derived local body name must agree with the actual feature")
    properties = semantics.properties
    require(type(properties) is PartTextInput
            and all(isinstance(scope, Mapping) for scope in (
                properties.SummaryFields, properties.DocumentFields, properties.ConfigurationFields,
            )),
            "local import properties require three typed literal text bags")
    return ImportedLabels(name, configuration.name, semantics.feature_name), semantics.body_name, properties


def make_document(name, points, levels, light):
    presentation = {"kit.sw2026.ambient": asdict(light)} if light is not None else {}
    return CadDocument(
        CadSource("kit.neutral", "", ""), (Configuration("active", "Default", True),),
        (), (), (), (), (), (), brep=prism_model(name, points, levels), metadata=presentation,
    )


def empty_world(index, alive, mark=0):
    fields = dict.fromkeys((field.name for field in SCHEMAS[WORLD_KIND].current), 0)
    fields.update(alive=alive, current_id=mark, highest_id=mark)
    return Node(index, WORLD_KIND, fields)


def empty_local_history():
    events = (DeltaEvent("activate"), MarkEvent("activation", "activate", True),
              DeltaEvent("attach"), MarkEvent("geometry", "attach", True))
    marks = allocate_marks(Session(1, 1, events, (), EPOCH, 0))
    selected, activation, initial = marks.kernel_index_order
    world, root_index, current, active, first = range(1, 6)
    identifiers = {selected: (current, active, 0), initial: (first, 0, active), activation: (active, first, current)}
    histories = []
    for mark in marks.transmit_order:
        index, previous, following = identifiers[mark]
        record = Node(index, PMARK_KIND, {"preceding": previous, "first_following": following,
                                        "next_sibling": 0, "prev_sibling": 0, "n_new_nodes": 0, "n_del_nodes": 0,
                                        "n_copy_mod_nodes": 0, "delta_key": mark.delta_key,
                                        "delta_is_forward": 0, "id": mark.mark_id})
        if mark.delta_key:
            rollback = Rollback((), empty_world(world, int(mark is selected)))
        else:
            rollback = None
        histories.append(History(record, rollback))
    partition = Partition((empty_world(world, 1, selected.mark_id),),
                          Node(root_index, PARTITION_KIND, {"current_pmark": current, "highest_id": selected.mark_id}),
                          tuple(histories))
    return marks, frame_payloads(write_payloads(partition))


def make_owned_nodes(model, name, feature_id, atom_id, body_stamp):
    require_neutral_prism(model)
    topology, next_id = complete_topology(topology_nodes(model, None))
    body = topology[0].ref
    encoded_name = name.encode("utf-16-le")
    units = unpack("<" + "H" * (len(encoded_name) // 2), encoded_name)
    installs = (
        Install(body, "ATOM_ID_2001", (None, (atom_id,))),
        Install(body, "LAST_BODY_MODIFYING_FEATURE_ID", (None, (feature_id,))),
        Install(body, "SWIMPLICITBODYNAME_ID_U", (units, None)),
        Install(body, "ENT_TIME_STAMP_2001", (None, (body_stamp,))),
        Install(body, "BODY_RECIPE_2001", (None, None)),
    )
    attributes = attach_attributes(topology, body, installs, next_id)
    declarations = tuple(node for row in installs for node in RECTANGLE_DEFINITION_BY_NAME[row.definition].nodes(0))
    draft = (*attributes.owners, *declarations, *attributes.chains)
    indices = {item.ref: index for index, item in enumerate(draft, start=1)}
    require(len(indices) == len(draft), "local attributes and surfaces need distinct wire identities")
    nodes = []
    for item in draft:
        fields = index_fields(item.fields, indices)
        if item.kind == BODY:
            fields["highest_node_id"] = attributes.next_identifier - 1
        nodes.append(Node(indices[item.ref], item.kind, fields))
    return tuple(nodes)


def make_streams(system, feature, recipe, headers, labels, local, partition):
    graph_nodes = (*system.FeatureValues, feature)
    definition = MakePartDef(recipe.DefinitionValue, recipe.DensityValue)
    keys = tuple(KeywordFeature(node.FieldsValue["f08"], ReadNativeName(node),
                                "Imported" if node is feature else node.ClassValue.NameValue,
                                "Feature", (), (), None, None) for node in graph_nodes)
    configs = tuple(KeywordConfig(node.FieldsValue["f08"], ReadNativeName(node), "") for node in system.ConfigValues)
    keywords = MakeKeywords(labels.NameValue, recipe.HeaderValue.ModifiedAt, configs, keys)
    streams, _, _ = EmitPartArchive(system, graph_nodes, headers, definition, recipe, keywords,
                                     BodyMapFields={"n": 0, "fcd8": []})
    return streams | {LOCAL: local, PARTITION: partition}


def make_part(document, destination, mode, completed=False, *, feature_name=DEFAULT_FEATURE_NAME, semantics=None):
    document.AssertValid()
    require(mode in MODES and str(document.units) == "mm" and
            set(document.metadata) <= {"kit.sw2026.ambient"} and
            not (document.assembly or document.DrawingValue or document.bodies or document.feature_timeline
                 or document.parameters or document.support_planes or document.sketches or document.selections
                 or document.meshes or document.materials or document.brep_payloads),
            "the local-body diagnostic requires a standalone neutral millimetre boundary")
    name = PureWindowsPath(destination).stem
    configuration, = document.configurations
    require(configuration.active and configuration.parent_id is None and not (
        configuration.overrides or configuration.suppressed_feature_ids or configuration.attributes
    ), "local import requires an active neutral configuration without unowned fields")
    labels, body_name, properties = import_labels(name, configuration, feature_name, semantics)
    recipe = MakePartRecipe(labels, EPOCH)
    recipe = replace(recipe, OutputValue=SelfFileInput(destination, EPOCH), PropertiesValue=properties)
    allocator = PersistentIds()
    system = MakePartBaseMut(recipe, labels, allocator)
    history = MakeImportHist(recipe.TargetValue.FileVersion, (ImportEvent.KActivation, ImportEvent.KLocalAttach))
    feature, atom_id = BindImportMut(system, allocator, recipe.TargetValue, labels.FeatureName, history.MarkIds)
    if "kit.sw2026.ambient" in document.metadata:
        light = AmbientInput(**document.metadata["kit.sw2026.ambient"])
        AttachAmbientMut(system.RootValue, light, recipe.TargetValue, allocator, EPOCH)
    SetCfgStampMut(system.ConfigValues[0], allocator)
    headers = MakePartHeaders(system, recipe, allocator)
    body_stamp = headers[0].FieldsValue["f44"] + 1
    for header in headers[:2]:
        header.FieldsValue["f44"] = body_stamp
        logs = header.FieldsValue["f20"].FieldsValue
        logs["items"] += (MakeRootLog(feature, recipe.HeaderValue),)
    if completed:
        FinishImportMut(system, feature, headers, recipe)
    if mode == "Owned":
        nodes = make_owned_nodes(document.brep, body_name, feature.FieldsValue["f08"], atom_id, body_stamp)
        typed = tuple(XmtNode(node.index, node.kind, node.fields) for node in nodes)
    else:
        typed = MakeLocalPrism(document.brep)
    local = EncodeLocalBody(labels.FeatureName, typed)
    streams = make_streams(system, feature, recipe, headers, labels, local, history.BytesValue)
    return BuildSldprt(streams, FormatVersion=4), streams


def verify_part(blob, streams):
    archive = SldprtArchive.from_bytes(blob)
    require(archive.streams == streams, "compound document changed its logical streams")
    local = decode(archive.require(LOCAL))
    link = ReadNativeLink(archive, 0)
    feature, = (node for node in link.ResolvedValue.RootsValue if node.ClassValue.NameValue == FEATURE_CLASS)
    atom, = (row["o"] for row in link.ConfigValue.RootValue.FieldsValue["fd88"]["atoms"])
    partition = read_partition(archive.require(PARTITION))
    require(feature.FieldsValue["local_storage_key"] == local.storage_key == ReadNativeName(feature)
            and feature.FieldsValue["f528"]["items"][0]["o"] is atom
            and atom.FieldsValue["f12c"] == atom.FieldsValue["f130"] == feature.FieldsValue["f08"]
            and feature.FieldsValue["f3d0"].FieldsValue["f18"] == partition.nodes[0].fields["current_id"]
            and partition.nodes[0].fields["body"] == 0, "generated import owners disagree on readback")
    nodes, _ = decode_local(local.kernel_stream)
    require(_render_local(nodes) == local.kernel_stream and frame_payloads(write_payloads(partition)) == streams[PARTITION],
            "generated local kernel or rollback bytes changed")
    return {"feature": ReadNativeName(feature), "feature_id": feature.FieldsValue["f08"],
            "atom_id": atom.FieldsValue["f140"], "kernel": fingerprint(local.kernel_stream), "kernel_nodes": len(nodes),
            "streams": {key: fingerprint(value) for key, value in streams.items()}}


def batch(native_root, light=None, completed=False):
    repository = Path(__file__).resolve().parents[4]
    tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    audit = BuildAudit(repository / "re/tooling/sw2026/serial/defs")
    audit.BeginBuild()
    running = True

    def guard(event, args):
        if running:
            audit.InspectEvent(event, args)
            if event.startswith("socket.") or event == "ctypes.dlopen":
                raise PermissionError(f"imported part construction attempted {event}")

    sys.addaudithook(guard)
    result = {}
    try:
        for shape, (points, levels, geometry) in CASES.items():
            for mode in MODES:
                name = shape + mode
                model = make_document(shape, points, levels, light)
                destination = str(native_root / (name + ".SLDPRT"))
                blob, streams = make_part(model, destination, mode, completed)
                details = verify_part(blob, streams)
                model_data = json.dumps(ToData(model), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
                volume, area, center = geometry
                result[name] = (blob, {**details, **fingerprint(blob), "shape": shape, "mode": mode, "native_path": destination,
                                       "neutral_sha256": sha256(model_data).hexdigest(),
                                       "expected_si": {"volume_m3": volume / 1e9, "area_m2": area / 1e6,
                                                        "com_m": tuple(coordinate / 1000 for coordinate in center),
                                                        "corners_m": tuple((x / 1000, y / 1000, z / 1000)
                                                                           for z in levels for x, y in points),
                                                        "edges": 3 * len(points), "faces": 2 + len(points)}})
    finally:
        running = False
    require(len({len(blob) for blob, _ in result.values()}) >= 2 and not audit.DeniedReads,
            "construction fails input-dependent length or runtime read checks")
    return result, len(audit.DeniedReads)


if __name__ == "__main__":
    parser = ArgumentParser(description="Generate complete local-body part candidates without original files")
    parser.add_argument("native_root", type=PureWindowsPath)
    parser.add_argument("--artifacts", type=Path)
    parser.add_argument("--ambient", action="store_true")
    parser.add_argument("--completed", action="store_true")
    args = parser.parse_args()
    results, denied = batch(args.native_root, AUTHORED_AMBIENT if args.ambient else None, args.completed)
    if args.artifacts:
        destination = args.artifacts.resolve()
        require(not destination.exists() and not destination.is_relative_to(Path(__file__).resolve().parents[4]),
                "choose an unused destination outside the repository")
        destination.mkdir(parents=True)
        for name, (blob, _) in results.items():
            (destination / (name + ".SLDPRT")).write_bytes(blob)
    print(json.dumps({"schema": "kit.sw2026.generated-imported-local-part.v1", "build_operator_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
                      "authored_ambient": args.ambient,
                      "modeled_completed_update": args.completed,
                      "runtime_input_file_reads": denied, "native_acceptance": False, "heldout_payloads_read": 0,
                      "cases": {name: data for name, (_, data) in results.items()}}, indent=2, sort_keys=True, allow_nan=False))
