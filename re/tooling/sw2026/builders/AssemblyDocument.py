from __future__ import annotations

from dataclasses import dataclass

from Streams import StreamDoc, store_rooted
from builders.Assembly import initial_assembly_features, initial_assembly_model, initial_configuration, store_empty_mates
from builders.Definition import assembly_definition, definition_stream
from builders.Metadata import FILE_VERSION, biography, fields, header, history, rooted_metadata_streams
from builders.Model import PersistentIds, configuration_manager
from builders.Styles import detail_definitions
from builders.Units import unit_table_profile
from defs.ConfigPart import store_config_state
from defs.ResolvedCore import store_resolved_state

CONFIG = "Contents/Config-0"
MODEL_HEADER = CONFIG + "-ModelHeader"
RESOLVED = CONFIG + "-ResolvedFeatures"
MATES = CONFIG + "-MatesList"
MANAGER = "Contents/CMgr"
DEFINITION = "Contents/Definition"
METADATA = ("Header2", MODEL_HEADER, "_MO_VERSION_19000/Biography", "_MO_VERSION_19000/History")


@dataclass(frozen=True)
class EmptyAssembly:
    streams: dict[str, bytes]
    config_map_count: int
    resolved_map_count: int


def _header_streams(*, registry, name, root, configuration, ids, provenance, presentation):
    created, modified = (provenance[key] for key in ("created_at", "modified_at"))
    stamp = {"status": 0, "user_index": 0, "company_index": 0, "timestamp": created, "comment": provenance["comment"]}
    values = {
        "next_id": ids.next_id,
        "user_names": [provenance["author"]],
        "company_names": [provenance["company"]],
        "revision_logs": [{"object_id": root["f08"], "name": name, "stamps": [stamp]}],
        "created_at": created, "modified_at": modified, "updated_at": modified, "component_count": 0,
        "update_stamp": 101, "body_stamp": 101, "license_flags": 0, "license_type": 0,
    }
    model_header = header(model_present=True, **values)
    result = rooted_metadata_streams(
        registry=registry, header2=header(model_present=False, **values),
        model_headers={configuration["f08"]: model_header},
        biography_record=biography(),
        history_record=history(
            states=[{"file_version": FILE_VERSION, "date_codes": [{"build_code": provenance["originating_build_code"], "native_save": False}], "stamp": stamp}],
            failure_severity=0, minimum_free_memory=0xFFFFFFFF,
            license_origin=provenance["license_origin"], language_id=presentation["language_id"],
            cjk_saved=presentation["cjk_saved"], cjk_warning=False,
        ),
    )
    return result, model_header


def construct_empty_assembly(*, registry, request) -> EmptyAssembly:
    fields(request, "empty assembly", ("name", "configuration_name", "origin_name", "mate_group_name", "provenance", "target", "presentation"))
    name, presentation, provenance = (request[key] for key in ("name", "presentation", "provenance"))
    fields(presentation, "assembly presentation", ("styles", "units", "definition", "assembly_features", "language_id", "cjk_saved"))
    fields(provenance, "assembly provenance", ("author", "company", "created_at", "modified_at", "comment", "originating_build_code", "license_origin"))
    target = fields(request["target"], "assembly target", ("date_code", "parasolid_version"))
    ids = PersistentIds()
    model = initial_assembly_model(name=name, allocator=ids, detail_definitions=detail_definitions(**presentation["styles"]), document_units=unit_table_profile(**presentation["units"]))
    manager = configuration_manager(owner=model, names=[request["configuration_name"]], updated_at=provenance["modified_at"], configuration_builder=initial_configuration, **target)
    features = initial_assembly_features(owner=model, allocator=ids, created_at=provenance["created_at"], origin_name=request["origin_name"], mate_group_name=request["mate_group_name"], **presentation["assembly_features"], **target)
    result, model_header = _header_streams(registry=registry, name=name, root=model, configuration=manager["f360"], ids=ids, provenance=provenance, presentation=presentation)
    config, state = store_config_state(StreamDoc(CONFIG, {"model_header": model_header}, [model]), registry, FILE_VERSION)
    context = {"model_compressed_stream": 1, "model_is_part": 0, "cmgr_f658": manager["f658"]}
    resolved, final_map = store_resolved_state(StreamDoc("resolved", {"base": state.count, "context": context}, features), registry, FILE_VERSION, seed=state)
    options = dict(presentation["definition"])
    options["tessellation"] = tuple(options["tessellation"])
    result.update({
        CONFIG: config,
        MANAGER: store_rooted(StreamDoc("rooted", {"base": 1}, [manager]), registry, FILE_VERSION),
        RESOLVED: resolved,
        MATES: store_empty_mates(registry=registry, resolved_map=final_map, mate_group=features[-1]),
        DEFINITION: definition_stream(registry=registry, document=assembly_definition(**options)),
    })
    return EmptyAssembly(result, state.count, final_map.count)
