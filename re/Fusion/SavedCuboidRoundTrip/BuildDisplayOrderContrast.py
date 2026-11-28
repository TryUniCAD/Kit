import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

from convert import open_document
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.State.DecodeState import DecodeState
from convert.Formats.Fusion.BrepCodec.History.EmitJournal import EmitJournal
from convert.Formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal as EmitTypedJournal
from convert.Formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.Formats.Fusion.BrepCodec.Prism.Reading.ReadPrismGraph import ReadPrismGraph
from convert.Formats.Fusion.BrepCodec.Prism.Reading.ReadPrismRoles import ReadPrismRoles
from convert.Formats.Fusion.BrepCodec.Prism.Reading.ReadPrismWire import ReadPrismWire
from convert.Formats.Fusion.BrepCodec.Prism.Writing.EmitPrismRows import EmitPrismRows
from convert.Formats.Fusion.BrepCodec.Prism.Writing.PrismRecords import PrismRecords
from convert.Formats.Fusion.BrepCodec.Wire.CheckBrepRefs import CheckBrepRefs
from convert.Formats.Fusion.BrepCodec.Wire.EmitBrepHeader import EmitBrepHeader
from convert.Formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.Formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KEdgeCorners, KFaceCorners, KFirstEdge, KFirstFace,
)
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.BrepWorld import BrepWorld
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.GroupValue import GroupValue
from convert.Formats.Fusion.GraphicsCodec.Model.Values.EntityRef import EntityRef as DisplayRef
from interchange import CadDocument


def require(value, reason):
    if not value:
        raise ValueError(reason)


def digest(data):
    return sha256(data).hexdigest()


def role_box(corners, indexes):
    axes = tuple(zip(*(corners[index] for index in indexes), strict=True))
    return tuple(map(min, axes)) + tuple(map(max, axes))


def display_world(model):
    body = SelectExtrusion(BuildGraph(model)).BodyNode
    owner = DisplayRef(body.SegmentId, body.ObjectId)
    require(model.Graphics is not None, 'saved cuboid has no graphics scene')
    worlds = []
    for item in model.Graphics.Objects:
        group = item.Value
        if not isinstance(group, GroupValue) or not isinstance(group.WorldValue, BrepWorld):
            continue
        data = group.NodeData.DataValue
        if data is not None and data.EntityLink == owner:
            worlds.append(group.WorldValue)
    require(len(worlds) == 1, 'expected one graphics world for the live solid')
    return owner, worlds[0]


def display_roles(nodes, owner, corners, groups):
    boxes = tuple(role_box(corners, group) for group in groups)
    require(len(boxes) == len(set(boxes)) == len(nodes), 'display inventory is not bijective')
    roles, qualifiers = [], []
    for node in nodes:
        data = node.NodeData.DataValue
        require(
            data is not None and data.EntityLink == owner and node.LodMask == 0
            and node.Geometry is None and node.Bounds in boxes,
            'unsupported display leaf owner or content',
        )
        roles.append(boxes.index(node.Bounds))
        qualifiers.append(data.Qualifier)
    require(len(set(roles)) == len(set(qualifiers)) == len(nodes), 'aliased display roles or qualifiers')
    return tuple(roles)


def history_roles(payload):
    wire = ReadPrismWire(payload)
    roles = ReadPrismRoles(ReadPrismGraph(wire.Table))
    return tuple(roles.Edges[key] for key in sorted(roles.Edges)), tuple(
        roles.Faces[key] for key in sorted(roles.Faces)
    )


def reorder_records(records, edges, faces):
    source_indexes = list(range(len(records)))
    for first, roles in ((KFirstEdge, edges), (KFirstFace, faces)):
        source_indexes[first:first + len(roles)] = [first + role for role in roles]
    remap = {previous: current for current, previous in enumerate(source_indexes)}
    require(set(remap) == set(range(len(records))), 'history ordering is not a permutation')
    return tuple(
        replace(records[index], Fields=tuple(
            EntityRef(remap[value.Index])
            if isinstance(value, EntityRef) and value.Index >= 0 else value
            for value in records[index].Fields
        ))
        for index in source_indexes
    )


def emit_history(history, edges, faces):
    records = PrismRecords(history.Identity, history.TagSet, history.Frame, history.Tracking)
    ordered = reorder_records(records, edges, faces)
    CheckBrepRefs(ordered, history.Header.RootCount)
    data = (
        EmitBrepHeader(history.Stamp, history.Header.RootCount, True, history.Header.Scale)
        + EmitPrismRows(ordered)
        + EmitJournal(history.History, len(ordered))
    )
    if history.Header.IntWidth == 4:
        data = EmitTypedJournal(replace(ReadJournal(data), Header=history.Header))
    require(history_roles(data) == (edges, faces), 'emitted roles do not follow the separable display order')
    return data


def write_new(path, payload):
    with path.open('xb') as out:
        out.write(payload)


def report_new(path, report):
    write_new(path, (json.dumps(report, indent=2, sort_keys=True) + '\n').encode('utf-8'))


def worker(path, output):
    raw = path.read_bytes()
    document = CadDocument.from_json(raw.decode('utf-8'))
    require(set(document.metadata) == {'fusion.native_state', 'fusion.read_only'}, 'expected strict saved cuboid JSON')
    require(document.metadata['fusion.read_only'] is True, 'read-only source marker is required')
    state = document.metadata['fusion.native_state']
    require(state['version'] == 2, 'expected saved-state version 2')
    model = DecodeState(state['model'])
    require(isinstance(model, DocumentModel) and len(model.Bodies) == 1, 'expected one typed body')
    body, = model.Bodies
    history = body.History
    require(isinstance(history, PrismHistory), 'expected typed prism history')
    owner, world = display_world(model)
    corners = history.Frame.CornersCm
    edges = display_roles(world.EdgeNodes, owner, corners, KEdgeCorners)
    faces = display_roles(world.FaceNodes, owner, corners, KFaceCorners)
    canonical = EmitParsed(model)
    container = ReadContainer(canonical)
    part, = [part for part in container.Parts if part.Name == body.PartName]
    canonical_roles = history_roles(part.Payload)
    ordered_part = replace(part, Payload=emit_history(history, edges, faces))
    ordered = EmitContainer(replace(container, Parts=tuple(
        ordered_part if current.Name == part.Name else current for current in container.Parts
    )))
    changed = ReadContainer(ordered)
    require(replace(changed, Parts=container.Parts) == container, 'non-part container data changed')
    require(tuple(value.Name for value in changed.Parts) == tuple(value.Name for value in container.Parts),
            'part inventory changed')
    names = [before.Name for before, after in zip(container.Parts, changed.Parts, strict=True) if before != after]
    require(names == [part.Name], 'contrast must change only the generated history part')
    require(ReadDocument(canonical) == ReadDocument(ordered) == model, 'contrast changes typed model')
    for payload in (canonical, ordered):
        observed = open_document(payload, source_format='f3d', strict=True)
        require(replace(observed, source=document.source) == document, 'contrast changes strict neutral graph')
    write_new(output / 'Canonical.f3d', canonical)
    write_new(output / 'DisplayOrdered.f3d', ordered)
    report_new(output / 'Prepared.json', {
        'input_json_sha256': digest(raw), 'source_sha256': document.source.sha256,
        'canonical_sha256': digest(canonical), 'display_ordered_sha256': digest(ordered),
        'canonical_roles': canonical_roles, 'display_roles': (edges, faces),
        'changed_part': part.Name, 'typed_equal': True, 'strict_neutral_equal': True,
        'native_measured': False, 'requires_presentation_oracle': True,
    })


def main():
    parser = argparse.ArgumentParser(description='Prepare a typed saved cuboid history order contrast')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--source', type=Path)
    group.add_argument('--persisted', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.persisted is not None:
        worker(args.persisted, args.output)
        return
    args.output.mkdir(parents=True, exist_ok=False)
    original = args.source.read_bytes()
    document = open_document(original, source_format='f3d', strict=True)
    persisted = args.output / 'Document.json'
    write_new(persisted, document.to_json().encode('utf-8'))
    subprocess.run((sys.executable, '-B', __file__, '--persisted', str(persisted), '--output', str(args.output)),
                   check=True, timeout=90)
    model = ReadDocument(original)
    source = ReadContainer(original)
    body, = model.Bodies
    original_history, = [part.Payload for part in source.Parts if part.Name == body.PartName]
    source_roles = history_roles(original_history)
    report = json.loads((args.output / 'Prepared.json').read_bytes())
    report_new(args.output / 'SourceComparison.json', {
        'source_sha256': digest(original), 'source_history_roles': source_roles,
        'source_order_matches_display': source_roles == tuple(map(tuple, report['display_roles'])),
        'source_order_matches_canonical': source_roles == tuple(map(tuple, report['canonical_roles'])),
        'prepared_sha256': digest((args.output / 'Prepared.json').read_bytes()),
    })


if __name__ == '__main__':
    main()
