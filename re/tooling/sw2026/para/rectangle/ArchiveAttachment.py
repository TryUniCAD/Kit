from copy import deepcopy
from dataclasses import dataclass

from .Allocate import Update, require
from builders.ConfigurationHeader import CONFIGURATION_MANAGER_HEADER, configuration_manager_header, configuration_manager_header_stream
from builders.Metadata import FILE_VERSION
from convert.adapters.solidworks.Container.Format import KPartitionStream
from defs.ConfigPart import store_config_state
from defs.ResolvedCore import store_resolved
from para.Partition import frame_payloads, write_payloads
from para.Tracking import local_downstream_face_words, unsigned
from Streams import StreamDoc, load_rooted, store_rooted


CONFIG = "Contents/Config-0"
RESOLVED = CONFIG + "-ResolvedFeatures"
MODEL_HEADER = CONFIG + "-ModelHeader"
MANAGER = "Contents/CMgr"
ACTIVE_HEADER = "Header2"
REBUILT_EXTRUSION_STATUS = 3
CLEAR_UPDATE_STATUS_MASK = 0xFFFD7FF8
FORCE_REBUILD_NODE_FLAG = 0x20
PART_REBUILD_CALLBACK_NODE_FLAG = 0x8000


@dataclass(frozen=True)
class FeatureUpdate:
    advance_index: int
    second: int
    fraction: int
    geometry_notification: bool


def advance_stamp(initial, operations, event):
    index = event.advance_index
    require(type(index) is int and 0 <= index < len(operations) and operations[index] is Update.ADVANCE,
            "feature completion must select a current-header advance event")
    return unsigned(initial + operations[:index + 1].count(Update.ADVANCE), 32, "feature update stamp")


def apply_feature_updates(model, header, features, session, events):
    require(len(events) == len(features), "the origin, rectangular sketch and boss each need explicit completed updates")
    moments = tuple((event.second, event.fraction) for event in events)
    indices = tuple(event.advance_index for event in events)
    require(all(left < right for left, right in zip(indices, indices[1:])), "feature updates must occur in model order")
    require(all(left <= right for left, right in zip(moments, moments[1:]))
            and header["f70"] <= moments[0][0] <= moments[-1][0] <= session.update_second,
            "feature update clocks must follow document creation and update chronology")
    for feature, event in zip(features, events, strict=True):
        require(type(event.geometry_notification) is bool, "each feature update must state whether it published geometry")
        _, low, high, _, _, _ = local_downstream_face_words(event.second, event.fraction)
        feature.f.update(f29c=advance_stamp(header["f40"], session.update_events, event), f2a0=low, f2a4=high,
                         f0c=feature["f0c"] & CLEAR_UPDATE_STATUS_MASK)
    model["f1300"] = unsigned(model["f1300"] + sum(event.geometry_notification for event in events), 32, "geometry stamp")
    model["f0c"] &= CLEAR_UPDATE_STATUS_MASK


def archive_for_oracle(*, registry, child, plan, projection, session, feature_updates,
                       record_saved_body_count=False, record_rebuild_completion=False):
    require(type(record_saved_body_count) is bool and type(record_rebuild_completion) is bool,
            "saved body bookkeeping controls must be Boolean")
    require(KPartitionStream not in child.streams and child.manager_header is not None and child.model_header["f38"] is not None,
            "standalone oracle candidate requires a fresh path-bound child")
    require(child.configuration["f08"] == 0 and child.extrusion.feature["f538"] is None,
            "standalone oracle candidate admits one ordinary boss without an extra atom")
    require(projection.partition.history[0].mark.fields["id"] == plan.archive.feature_mark["f18"],
            "the projected rollback must belong to the same extrusion allocation")
    model, header, features, binding = deepcopy((child.model, child.model_header, child.features, plan.archive))
    origin, = (feature for feature in features if feature.cls == "moOriginProfileFeature_c")
    sketch, = (feature for feature in features if feature.cls == "moProfileFeature_c")
    boss, = (feature for feature in features if feature.cls == "moExtrusion_c")
    require(boss["f08"] == binding.feature_id and not model["fd88"]["atoms"] and not model["ffe0"] and model["fe38"] is None
            and not boss["has_f3d0"], "archive candidate requests a new attachment on the plan's ordinary extrusion")
    apply_feature_updates(model, header, (origin, sketch, boss), session, feature_updates)
    if record_rebuild_completion:
        require(any(event.geometry_notification for event in feature_updates),
                "a completed rebuild requires a modeled geometry notification")
        model["f2c"] |= FORCE_REBUILD_NODE_FLAG | PART_REBUILD_CALLBACK_NODE_FLAG
    atom_entries = binding.manager_registration["atoms"]
    require(len(atom_entries) == 1 and atom_entries[0]["o"] is binding.atom and binding.atom["f170"] == 0,
            "the captured model must own one ordinary visible body")
    snapshot = [{"k": binding.atom, "v": int(binding.atom["f170"] != 0)}]
    model["fd88"].update(binding.manager_registration, n6c=len(atom_entries), fa8=FILE_VERSION)
    model.f.update(fe38=binding.part_mark, f1010=1, ffe0=snapshot, nff4=len(snapshot))
    boss.f.update(has_f3d0=1, f3d0=binding.feature_mark, f3c0=0, f3c8=0, f580=0, f540=REBUILT_EXTRUSION_STATUS)
    header.f.update(binding.active_header_fields)

    manager_document, _ = load_rooted(child.streams[MANAGER], registry, 1, FILE_VERSION)
    manager, = manager_document.roots
    config = manager["f360"]
    require(not manager_document.tail and config is manager["f368"] and manager["f370"]["items"][0]["o"] is config,
            "configuration manager readback lost the generated active configuration")
    config["f860"] = header["f40"]
    if record_saved_body_count:
        config["f6f8"] = len(atom_entries)
    manager_bytes = store_rooted(manager_document, registry, FILE_VERSION)
    manager["owner"] = config["owner"] = model
    manager_header = configuration_manager_header(manager=manager, saved_at=child.manager_header["f60"])

    config_bytes, state = store_config_state(StreamDoc(CONFIG, {"model_header": header}, [model]), registry, FILE_VERSION)
    resolved = StreamDoc(RESOLVED, {"base": state.count, "context": {
        "model_compressed_stream": 1, "model_is_part": 1, "cmgr_f658": manager["f658"],
    }}, features)
    linked_header = store_rooted(StreamDoc(MODEL_HEADER, {"base": 1}, [header]), registry, FILE_VERSION)
    return child.streams | {
        CONFIG: config_bytes,
        RESOLVED: store_resolved(resolved, registry, FILE_VERSION, seed=state),
        MODEL_HEADER: linked_header,
        ACTIVE_HEADER: linked_header,
        MANAGER: manager_bytes,
        CONFIGURATION_MANAGER_HEADER: configuration_manager_header_stream(registry=registry, header=manager_header),
        KPartitionStream: frame_payloads(write_payloads(projection.partition)),
    }
