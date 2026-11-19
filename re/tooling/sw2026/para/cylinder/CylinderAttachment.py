from dataclasses import dataclass

from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHdrMut import WriteMgrHdrMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.BodyScope.MakeStockAtom import MakeStockAtom
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeMgrHeader import MakeMgrHeader
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Container.Format import KPartitionStream, KResolvedFeaturesStream
from para.rectangle.ArchiveAttachment import CLEAR_UPDATE_STATUS_MASK, REBUILT_EXTRUSION_STATUS, advance_stamp
from para.Tracking import body_match_tag, local_downstream_face_words, unsigned
from para.cylinder.ProjectCylinder import CylinderBodyTracking, project_cylinder
from para.rectangle.Allocate import allocate_marks, allocate_updates, positive_i32, require


CONFIG = "Contents/Config-0"
VERSION = 19000


@dataclass(frozen=True)
class GeneratedAttachment:
    streams: dict[str, bytes]
    file_bytes: bytes
    atom_id: int
    body_tag: int
    selected_mark: int
    activation_mark: int
    lateral_face_node_id: int


def mark_node(mark):
    return ArchiveNode(RuntimeClass("moPMarkRecord_c", 1), {"f18": mark.mark_id})


def bind_features(candidate, session, events):
    model = candidate.SystemValue.RootValue.FieldsValue
    header = candidate.HeaderValue.FieldsValue
    feature_set = (candidate.SystemValue.OriginValue.ProfileValue,
                   candidate.ProfileValue.ProfileValue, candidate.BossValue.FeatureValue)
    require(len(events) == len(feature_set), "provide one actual origin, profile and boss update")
    moments = tuple((event.second, event.fraction) for event in events)
    advances = tuple(event.advance_index for event in events)
    require(all(left < right for left, right in zip(advances, advances[1:]))
            and all(left <= right for left, right in zip(moments, moments[1:]))
            and (header["f70"], 0) <= moments[0] <= moments[-1] <= (session.update_second, session.update_fraction),
            "feature updates must follow model creation, order and update time")
    updates = []
    for entry, event in zip(feature_set, events, strict=True):
        require(type(event.geometry_notification) is bool, "feature geometry notifications must be explicit")
        stamp = advance_stamp(header["f40"], session.update_events, event)
        _, low, high, _, _, _ = local_downstream_face_words(event.second, event.fraction)
        updates.append((entry.FieldsValue, stamp, low, high))
    geometry_stamp = unsigned(model["f1300"] + sum(event.geometry_notification for event in events), 32, "model stamp")
    for fields, stamp, low, high in updates:
        fields.update(f29c=stamp, f2a0=low, f2a4=high, f0c=fields["f0c"] & CLEAR_UPDATE_STATUS_MASK)
    model["f1300"] = geometry_stamp
    model["f0c"] &= CLEAR_UPDATE_STATUS_MASK


def attach_cylinder_mut(candidate, session, feature_events, previous_face_allocations):
    require(KPartitionStream not in candidate.StreamsValue and candidate.CutValue is None, "expected a new circle part")
    root = candidate.SystemValue.RootValue
    model = root.FieldsValue
    manager = model["fd88"]
    boss = candidate.BossValue.FeatureValue
    feature = boss.FieldsValue
    require(not manager["atoms"] and manager["n6c"] == 0 and manager["fa8"] == 0
            and not model["ffe0"] and model.get("fe38") is None and feature.get("f538") is None
            and not any(feature[k] for k in ("has_f528", "has_f530", "n494", "has_f3d0")),
            "source must have an unused ordinary output and live-body map")
    marks, updates = allocate_marks(session), allocate_updates(session, candidate.HeaderValue.FieldsValue)
    body_tag = body_match_tag(positive_i32(session.first_tag, "body allocation tag"))
    tracking = CylinderBodyTracking(body_tag, updates.body)
    projection = project_cylinder(candidate, session, previous_face_allocations, tracking=tracking)
    atom_id = projection.reserved_body_atom_id
    atom = MakeStockAtom(boss, atom_id)
    atom.FieldsValue.update(f180=body_tag, f1b0=body_tag, f188=1)
    bind_features(candidate, session, feature_events)
    rows = [{"o": atom}]
    manager.update(f260=atom_id, n6c=len(rows), fa8=VERSION, atoms=rows)
    visibility = [{"k": atom, "v": int(atom.FieldsValue["f170"] != 0)}]
    model.update(fe38=mark_node(marks.activation), f1010=1, nff4=len(visibility), ffe0=visibility)
    feature.update(has_f528=1, f528={"n": len(rows), "items": [{"o": atom}]},
                   f498=[{"v": atom_id}], n494=len(rows),
                   has_f3d0=1, f3d0=mark_node(marks.selected), f3c0=0, f3c8=0, f580=0,
                   f540=REBUILT_EXTRUSION_STATUS)
    header = candidate.HeaderValue
    for owner in (header, candidate.TopHeader):
        owner.FieldsValue.update(f40=updates.saved_update, f44=updates.saved_body, f48=session.update_second)
    config = candidate.CurrentConfig
    config.FieldsValue["f860"] = updates.saved_update
    cmgr = candidate.SystemValue.ManagerValue
    cmgr_header = MakeMgrHeader(cmgr, candidate.ManagerHeader.FieldsValue["f60"])
    config_bytes, model_graph = WriteConfigMut(root, VERSION, header)
    resolved_bytes, _ = WriteResolMut(candidate.ResolvedValue.RootsValue, None, VERSION, model_graph.MapValue,
                                    {"model_compressed_stream": 1, "model_is_part": 1,
                                     "cmgr_f658": cmgr.FieldsValue["f658"]})
    streams = candidate.StreamsValue | {
        CONFIG: config_bytes,
        KResolvedFeaturesStream: resolved_bytes,
        CONFIG + "-ModelHeader": WriteHeadGraph(header, VERSION),
        "Header2": WriteHeadGraph(candidate.TopHeader, VERSION),
        "Contents/CMgr": WriteCmgrMut(cmgr, VERSION),
        "Contents/CMgrHdr2": WriteMgrHdrMut(cmgr_header, VERSION)[0],
        KPartitionStream: projection.stream(),
    }
    return GeneratedAttachment(streams, BuildSldprt(streams, FormatVersion=4), atom_id, body_tag,
                               marks.selected.mark_id, marks.activation.mark_id, projection.lateral_face_node_id)
