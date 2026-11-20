from argparse import ArgumentParser
from codecs import lookup
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
from struct import unpack
import sys

from BuildLocalBodyKernel import CASES, make_nodes, prism_model, require_closed_unattributed, require_neutral_prism
from LocalBodyEnvelope import LOCAL, PARTITION, LocalBody, decode, encode
from LocalBodyKernel import BODY, _render_local, decode_local, encode_closed_local, fingerprint
from ReplayImportedBaseBody import require
from builders.EmptyPartition import PMARK_KIND, PARTITION_KIND, WORLD_KIND
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHdrMut import WriteMgrHdrMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.BodyScope.MakeStockAtom import MakeStockAtom
from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import FeatureInstant
from convert.adapters.solidworks.Archive.Construction.Chronology.MakeFeatTime import MakeFeatTime
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Header.MakeRootLog import MakeRootLog
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import KeywordConfig
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import KeywordFeature
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeBiography import MakeBiography
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeFreshHist import MakeFreshHist
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeywords import MakeKeywords
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import KAtomLists, KAtomWords
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import InitFeatureMut
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import MakePartHeaders
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import MakePartDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import KResolvedFeaturesStream, KeywordsStream
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
from para.rectangle.ArchiveAttachment import CLEAR_UPDATE_STATUS_MASK, FORCE_REBUILD_NODE_FLAG, PART_REBUILD_CALLBACK_NODE_FLAG
from para.rectangle.Geometry import topology_nodes
from para.rectangle.RectanglePartition import complete_topology
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit


VERSION = 19000
FEATURE_CLASS = "moBaseBody_c"
EPOCH = 1790000000
MODES = ("Bare", "Owned")
AUTHORED_AMBIENT = AmbientInput("Import ambient", "KitImportAmbient", 0.5, 0.5, 0.0, 0x00FFFFFF)


@dataclass(frozen=True)
class ImportedLabels:
    NameValue: str
    ConfigName: str
    FeatureName: str
    PlaneName: str = "Front Plane"
    AxisValue: str = "z"
    SketchName: str = ""


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


def mark_node(mark):
    return ArchiveNode(RuntimeClass("moPMarkRecord_c", 1), {"f18": mark.mark_id})


def bind_feature(system, allocator, target, labels, marks):
    owner = system.RootValue
    feature = ArchiveNode(RuntimeClass(FEATURE_CLASS, 1), {})
    InitFeatureMut(feature, labels.FeatureName, owner, target, allocator)
    fields = feature.FieldsValue
    fields.update(dict.fromkeys(KAtomWords, 0))
    fields.update({field: [] for field in KAtomLists})
    fields.update(f35c=0, f368={"n": 0, "items": []}, f388={"n": 0, "items": []}, f538=None,
                  f4a0=1, f6e0=None, f758=None, f780={"n": 0, "items": []}, f7a0=0,
                  source_filename="", local_body_switch=1, local_storage_key=labels.FeatureName,
                  segment_mesh_count=0, segment_mesh_ids=[])
    manager = owner.FieldsValue["fd88"]
    atom_id = manager["f260"] + 1
    atom = MakeStockAtom(feature, atom_id)
    atom.FieldsValue["f188"] = 1
    entries = [{"o": atom}]
    manager.update(f260=atom_id, n6c=len(entries), atoms=entries, fa8=VERSION)
    system.ManagerValue.FieldsValue["f658"] = 1
    owner.FieldsValue.update(fe38=mark_node(marks.activation), f1010=1)
    fields.update(has_f528=1, f528={"n": len(entries), "items": entries}, n494=len(entries), f498=[{"v": atom_id}],
                  has_f3d0=1, f3d0=mark_node(marks.selected), f3c0=0, f3c8=0, f580=0)
    return feature, atom_id


def make_owned_kernel(model, name, feature_id, atom_id, body_stamp):
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
    return encode_closed_local(tuple(nodes))


def make_streams(system, feature, recipe, headers, labels, local, partition):
    header, top, manager_header = headers
    graph_nodes = (*system.FeatureValues, feature)
    config, graph = WriteConfigMut(system.RootValue, VERSION, header)
    resolved, _ = WriteResolMut(graph_nodes, {"n": 0, "fcd8": []}, VERSION, graph.MapValue, {
        "model_is_part": 1, "model_compressed_stream": 1, "cmgr_f658": system.ManagerValue.FieldsValue["f658"],
    })
    definition = MakePartDef(recipe.DefinitionValue, recipe.DensityValue)
    keys = tuple(KeywordFeature(node.FieldsValue["f08"], ReadNativeName(node),
                                "Imported" if node is feature else node.ClassValue.NameValue,
                                "Feature", (), (), None, None) for node in graph_nodes)
    configs = tuple(KeywordConfig(node.FieldsValue["f08"], ReadNativeName(node), "") for node in system.ConfigValues)
    return {
        "Header2": WriteHeadGraph(top, VERSION), "Contents/Config-0-ModelHeader": WriteHeadGraph(header, VERSION),
        "Contents/Config-0": config, "Contents/CMgr": WriteCmgrMut(system.ManagerValue, VERSION),
        "Contents/CMgrHdr2": WriteMgrHdrMut(manager_header, VERSION)[0], KResolvedFeaturesStream: resolved,
        "Contents/Definition": WriteModelDef(definition).OutputValue,
        "_MO_VERSION_19000/Biography": WriteHistMut(MakeBiography(), VERSION)[0],
        "_MO_VERSION_19000/History": WriteHistMut(MakeFreshHist(recipe.HistoryValue), VERSION)[0],
        KeywordsStream: MakeKeywords(labels.NameValue, recipe.HeaderValue.ModifiedAt, configs, keys),
        LOCAL: encode(local), PARTITION: partition,
    }


def publish_completed_update(system, headers, feature, recipe):
    retained = (system.OriginValue.ProfileValue, feature)
    active_header, top_header, _ = headers
    stamp = active_header.FieldsValue["f40"]
    clock = MakeFeatTime(FeatureInstant(recipe.HeaderValue.UpdatedAt, 0))
    for owner in retained:
        stamp += 1
        fields = owner.FieldsValue
        fields.update(clock, f29c=stamp, f2b8=recipe.TargetValue.FileVersion, f2bc=recipe.TargetValue.DateCode)
        fields["f0c"] &= CLEAR_UPDATE_STATUS_MASK
    model = system.RootValue.FieldsValue
    model["f0c"] &= CLEAR_UPDATE_STATUS_MASK
    model["f2c"] |= FORCE_REBUILD_NODE_FLAG | PART_REBUILD_CALLBACK_NODE_FLAG
    configuration = system.ConfigValues[0].FieldsValue
    configuration["f860"] = stamp
    configuration["f6f8"] = len(model["fd88"]["atoms"])
    for header in (active_header, top_header):
        header.FieldsValue["f40"] = stamp


def make_part(document, destination, mode, completed=False):
    document.AssertValid()
    require(mode in MODES and str(document.units) == "mm" and
            set(document.metadata) <= {"kit.sw2026.ambient"} and
            not (document.assembly or document.DrawingValue or document.bodies or document.feature_timeline
                 or document.parameters or document.support_planes or document.sketches or document.selections
                 or document.meshes or document.materials or document.brep_payloads),
            "the local-body diagnostic requires a standalone neutral millimetre boundary")
    name = PureWindowsPath(destination).stem
    configuration, = document.configurations
    labels = ImportedLabels(name, configuration.name, "Imported geometry")
    recipe = MakePartRecipe(labels, EPOCH)
    recipe = replace(recipe, OutputValue=SelfFileInput(destination, EPOCH))
    allocator = PersistentIds()
    system = MakePartBaseMut(recipe, labels, allocator)
    marks, partition = empty_local_history()
    feature, atom_id = bind_feature(system, allocator, recipe.TargetValue, labels, marks)
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
        publish_completed_update(system, headers, feature, recipe)
    if mode == "Owned":
        raw = make_owned_kernel(document.brep, labels.FeatureName, feature.FieldsValue["f08"], atom_id, body_stamp)
    else:
        nodes = make_nodes(document.brep)
        require_closed_unattributed(nodes)
        raw = _render_local(nodes)
    streams = make_streams(system, feature, recipe, headers, labels, LocalBody(labels.FeatureName, raw), partition)
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
