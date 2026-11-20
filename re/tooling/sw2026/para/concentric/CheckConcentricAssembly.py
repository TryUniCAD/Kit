from dataclasses import replace
from hashlib import sha256
from math import dist, fsum, isclose
from pathlib import Path, PureWindowsPath
import argparse
import codecs
import json
import sys

from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Assembly.Assembly import DecodeNativeAsm
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireNode
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarContext
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import ReadVector
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedMates.CheckMateIds import CheckMateIds
from convert.adapters.solidworks.Core.TypedMates.CheckMateMode import CheckMateMode
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CheckCylFacet import CheckCylFacet
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CheckCylIds import CheckCylIds
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CheckCylMode import CheckCylMode
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CheckCylPair import CheckCylPair
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CheckCylRefs import CheckCylRefs
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CylChild import CylChild
from convert.adapters.solidworks.Core.TypedMates.Cylinders.PickCylFace import PickCylFace
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylEnd import ReadCylEnd
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylNodes import ReadCylNodes
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylOwner import ReadCylOwner
from convert.adapters.solidworks.Core.TypedMates.ReadFixedFlags import ReadFixedFlags
from convert.adapters.solidworks.Core.TypedMates.ReadMateFrame import ReadMateFrame
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
from interchange.serialization.Deserialize import FromData
from para.concentric.ConcentricAssembly import prepare_concentric
from para.rectangle.Allocate import DeltaEvent, MarkEvent, Session, Update
from para.rectangle.ArchiveAttachment import FeatureUpdate

CONFIG = "Contents/Config-0"


def context(archive, link):
    info = DecodeNativeAsm(archive)
    return PlanarContext(link.ConfigValue.RootValue,
                        {item.feature_id: item for item in info.occurrences},
                        {item.object_id: item for item in info.definitions}, {})


def read_child(attachment):
    child_bytes = attachment.candidate.BytesValue
    archive = SldprtArchive.from_bytes(child_bytes)
    link = ReadNativeLink(archive, 0)
    nodes = ReadCylNodes(archive)
    face, geometry, _ = PickCylFace(nodes)
    atom = attachment.atom_id
    feature, arc = ReadCylOwner(link, atom)
    return CylChild(link, nodes, face, geometry, feature, arc, atom, sha256(child_bytes).hexdigest())


def read_rim_centers(child):
    nodes, side = child.NodesValue, child.FaceValue
    loops = WalkXmtChain(nodes, side.Integer("loop"), 15, PreviousField=None,
                         OwnerField="face", OwnerValue=side.IndexValue)
    assert len(loops) == 2
    centers = []
    for index in loops:
        fin = RequireXmt(nodes, nodes[index].Integer("halfedge"), 17)
        edge = RequireXmt(nodes, fin.Integer("edge"), 16)
        circle = RequireXmt(nodes, edge.Integer("curve"), 31)
        centers.append(ReadXmtVector(circle, "centre"))
    return tuple(centers)


def check_signed_extent(endpoint, local_axis, rims, active, support):
    assert endpoint.LocalAxisValue == local_axis, "emitted local axis differs from the ordered signed request"
    matrix = ReadMateFrame(endpoint.ItemValue.transform)
    centers = tuple(tuple(matrix[12 + i] + fsum(value * matrix[4 * axis + i]
                                                 for axis, value in enumerate(point))
                          for i in range(3)) for point in rims)
    anchor, other = centers
    assert dist(anchor, endpoint.OriginValue) <= 1e-12 and dist(other, endpoint.OriginValue) > 1e-12
    delta = tuple(value - origin for value, origin in zip(other, endpoint.OriginValue, strict=True))
    span = fsum(value * direction for value, direction in zip(delta, endpoint.AxisValue, strict=True))
    assert active["f50"] == 2 and active["fb0"] == 0.0 and isclose(active["fb8"], span, rel_tol=1e-12, abs_tol=1e-12), (
        "emitted signed extent differs from the actual transformed rims"
    )
    assert ReadVector(support["fd0"]) == endpoint.OriginValue and ReadVector(support["fe8"]) == endpoint.AxisValue, (
        "detached support does not retain the signed active carrier"
    )
    component = RequireNode(support["f58"], "moCompRefCylinder_c")
    cylinder = RequireNode(component.FieldsValue["ff8"], "moRefCylinder_c").FieldsValue
    assert ReadVector(cylinder["f6f8"]) == endpoint.OriginValue and ReadVector(cylinder["f710"]) == endpoint.AxisValue


def verify_emission(raw, attachment, alignment, locked, fixed, occurrence_names, *, expected_local_axes=None):
    archive = SldprtArchive.from_bytes(raw)
    linked = ReadNativeLink(archive, 0)
    cfg, resol = linked.ConfigValue, linked.ResolvedValue
    context_value = context(archive, linked)
    stream = archive.require(CONFIG + "-MatesList")
    graph = ReadMatesMut(stream, resol)
    mate, = graph.RootsValue
    assert mate.ClassValue.NameValue == "moMateConcentric"
    assert mate.FieldsValue["f3b4"] == alignment and mate.FieldsValue["f4b8"] == int(locked)
    fixed_flags = [row["fixed"] for row in ReadFixedFlags(context_value)]
    assert fixed_flags == [index == fixed for index in range(2)]
    CheckMateMode(mate)
    try:
        CheckCylMode(mate)
    except ValueError as error:
        assert str(error) == "concentric mate is outside the ordinary solved position profile"
    else:
        raise AssertionError("pre-solve candidate unexpectedly claims the solved profile")
    CheckMateIds(graph.RootsValue, linked)
    CheckCylIds(mate)
    CheckCylRefs(mate, context_value.ModelNode, cfg.HeaderValue)
    child = read_child(attachment)
    active = [row["o"] for row in mate.FieldsValue["f410"]]
    support = [row["o"] for row in mate.FieldsValue["f3c8"]]
    selected = tuple(ReadCylEnd(context_value, child, wrapper, mate.FieldsValue["f08"], index)
                     for index, wrapper in enumerate(active))
    emitted_names = tuple(f"{endpoint.ItemValue.name}-{endpoint.ItemValue.reference_number}" for endpoint in selected)
    assert emitted_names == occurrence_names
    CheckCylPair(selected, alignment)
    for wrapper in support:
        CheckCylFacet(wrapper, child)
        fields = wrapper.FieldsValue
        assert tuple(fields[key] for key in ("fb0", "fb8", "fc0", "fc8")) == (-1.0, 1.0, 1.0, -1.0)
        assert not fields["has_f108"]
    keeper_files = []
    tags = []
    intervals = []
    if expected_local_axes is not None:
        assert len(expected_local_axes) == len(selected) == 2
        rims = read_rim_centers(child)
    for index, wrapper in enumerate(active):
        fields = wrapper.FieldsValue
        lower, upper = fields["fb0"], fields["fb8"]
        if expected_local_axes is None:
            assert lower == 0.0 and isclose(upper, attachment.candidate.PlanValue.DepthValue, rel_tol=1e-12)
        else:
            check_signed_extent(selected[index], expected_local_axes[index], rims, fields, support[index].FieldsValue)
        assert (fields["fc0"], fields["fc8"]) == (1.0, -1.0)
        intervals.append((lower, upper))
        face = fields["f58"].FieldsValue["fe8"].FieldsValue
        tag = face["f70"]
        assert tag == attachment.projection.lateral_face_tag
        tags.append(tag)
        rows = face["f10"]
        assert rows[2]["f08"] is rows[4]["f08"] is None
        assert [rows[index]["f08"].FieldsValue["f38"] for index in (1, 3)] == [1, 0]
        keeper_files.extend(rows[index]["f08"].FieldsValue["f10"]["f10"].FieldsValue["f08"] for index in (0, 1, 3))
    assert all(value is keeper_files[0] for value in keeper_files)
    assert ReadFileKey(keeper_files[0]) == ReadFileKey(child.LinkValue.ConfigValue.HeaderValue.FieldsValue["f38"])
    assert WriteMatesMut(graph.RootsValue, resol)[0] == stream
    config_bytes, config = WriteConfigMut(cfg.RootValue, 19000, cfg.HeaderValue)
    resolved_bytes, _ = WriteResolMut(resol.RootsValue, resol.ExtraFields, 19000, config.MapValue, resol.ContextValue)
    assert config_bytes == archive.require(CONFIG) and resolved_bytes == archive.require(CONFIG + "-ResolvedFeatures")
    assert all(item.ItemValue.configuration_id == 0 for item in selected)
    assert all(item.StampValue == attachment.candidate.HeaderValue.FieldsValue["f40"] for item in selected)
    assert all(item.RadiusValue == attachment.candidate.PlanValue.CircleValue.RadiusValue for item in selected)
    return {
        "maps": [graph.MapBase, graph.MapValue.CounterValue], "mate_bytes": len(stream),
        "mate_sha256": sha256(stream).hexdigest(), "alignment": alignment, "rotation_locked": locked,
        "child_sha256": child.SourceHash, "face_tags": tags, "kernel_node_id": child.FaceValue.Integer("node_id"),
        "body_atom_id": child.AtomValue, "occurrences": [item.ItemValue.feature_id for item in selected],
        "occurrence_names": occurrence_names, "fixed_flags": fixed_flags,
        "active_intervals": intervals, "detached_defaults_preserved": True,
        "world_origins": [item.OriginValue for item in selected], "world_axes": [item.AxisValue for item in selected],
        "round_tripped_linked_streams": 3, "solved_reader_refused_presolve": True,
        "root_recipe": "neutral document", "caps_follow_generated_lateral_loops": True,
        **({"local_axes": [item.LocalAxisValue for item in selected], "signed_rim_bounds_verified": True}
           if expected_local_axes is not None else {}),
    }


def schedule(written_at, case):
    events = (
        DeltaEvent("activation"), MarkEvent("activation", "activation", True),
        DeltaEvent("intervening"), MarkEvent("intervening", "intervening", False),
        DeltaEvent("geometry"), MarkEvent("geometry", "geometry", True),
    )
    updates = (Update.ADVANCE, Update.ADVANCE, Update.ADVANCE, Update.ATTACH_BODY, Update.TESSELLATE)
    return Session(1137 + 1148 * case, 26 + 91 * case, events, updates, written_at, 1159 * case)


def run(document, destination, written_at, case):
    document.AssertValid()
    model = ReadAsmModel(document)
    GetDocumentCaps(model.ChildDocument)
    for encoding in ("utf-16-le", "utf-16-be", "cp1252", "utf-8"):
        codecs.lookup(encoding)
    session = schedule(written_at, case)
    updates = tuple(FeatureUpdate(index, written_at, index + 1, True) for index in range(3))
    mate = model.GraphValue.mates[0]
    alignment = 1 if str(mate.alignment) == "aligned" else 2
    lock = mate.attributes["rotation_locked"]
    entities = {entity.id: entity for entity in model.GraphValue.mate_entities}
    names = {occurrence.id: occurrence.name for occurrence in model.Occurrences}
    occurrence_names = tuple(names[entities[identity].instance_path[0]] for identity in mate.entity_ids)
    active = True
    attempts = []

    def guard(event, value):
        if active and event in {"open", "subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect"}:
            attempts.append(event)
            raise RuntimeError("concentric construction attempted runtime access: " + event)

    sys.addaudithook(guard)
    try:
        bundle = prepare_concentric(document, destination, written_at, session, updates, 7 * case)
        repeat = prepare_concentric(document, destination, written_at, session, updates, 7 * case)
        assert bundle.assembly == repeat.assembly and bundle.attachment.file_bytes == repeat.attachment.file_bytes
        bad = replace(model.GraphValue.mate_entities[0], source_entity_id="invalid/face")
        wrong_graph = replace(model.GraphValue, mate_entities=(bad, *model.GraphValue.mate_entities[1:]))
        try:
            prepare_concentric(replace(document, assembly=wrong_graph), destination, written_at, session, updates, 7 * case)
        except ValueError as error:
            assert str(error) == "concentric neutral admission: selected neutral lateral face is absent or ambiguous"
        else:
            raise AssertionError("a foreign neutral face unexpectedly wrote a mate")
        receipt = verify_emission(bundle.assembly, bundle.attachment, alignment, lock, model.FixedIndex, occurrence_names)
        longer_graph = replace(model.GraphValue, mates=(replace(mate, name=mate.name + " axial travel"),))
        longer = prepare_concentric(replace(document, assembly=longer_graph), destination, written_at, session, updates, 7 * case)
        longer_stream = SldprtArchive.from_bytes(longer.assembly).require(CONFIG + "-MatesList")
        added_bytes = len(longer_stream) - receipt["mate_bytes"]
        assert added_bytes > 0
    finally:
        active = False
    assert not attempts
    result = {
        **receipt,
        "assembly_sha256": sha256(bundle.assembly).hexdigest(),
        "assembly_bytes": len(bundle.assembly),
        "runtime_io_attempts": len(attempts),
        "same_process_repeat_exact": True,
        "foreign_face_refused": True,
        "longer_mate_name_added_stream_bytes": added_bytes,
        "native_runs": 0,
    }
    return result, bundle


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("document", type=Path)
    parser.add_argument("--case", type=int, choices=(1, 2), required=True)
    parser.add_argument("--written-at", type=int, default=1815300301)
    parser.add_argument("--native-destination")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data = args.document.read_bytes()
    document = FromData(json.loads(data))
    model = ReadAsmModel(document)
    destination = args.native_destination
    if destination is None:
        destination = str(PureWindowsPath("C:/KitResearch", model.RootValue.name + ".SLDASM"))
    receipt, bundle = run(document, destination, args.written_at, args.case)
    if args.output:
        args.output.mkdir(exist_ok=False)
        (args.output / PureWindowsPath(destination).name).write_bytes(bundle.assembly)
        (args.output / (model.ChildValue.name + ".SLDPRT")).write_bytes(bundle.attachment.file_bytes)
    receipt["input_sha256"] = sha256(data).hexdigest()
    receipt["final_destination"] = destination
    print(json.dumps(receipt, indent=2, allow_nan=False, sort_keys=True))


if __name__ == "__main__":
    main()
