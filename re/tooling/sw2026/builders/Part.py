from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from Core import ArchiveError, Obj
from Streams import StreamDoc, store_rooted
from builders.Definition import definition_stream, part_definition
from builders.Extrude import live_blind_extrusion
from builders.Metadata import biography, fields, header, history, keywords, streams
from builders.Model import body_feature, component_plane, model_feature, part_graph
from builders.Sketch import PlaneFrame, closed_profile, origin_profile
from builders.Styles import detail_definitions
from builders.Units import unit_table_profile
from defs.ConfigPart import store_config_state
from defs.ResolvedCore import store_resolved


@dataclass(frozen=True, kw_only=True)
class PartConstruction:
    streams: dict[str, bytes]
    model: Obj
    features: tuple[Obj, ...]
    extrusion: object
    next_id: int
    configuration_map_count: int


def _rooted(*, registry, node):
    return store_rooted(StreamDoc("rooted", {"base": 1}, [node]), registry, 19000)


def _metadata(*, registry, document, provenance, presentation, graph, features, extrusion):
    stamp = {
        "status": 0, "user_index": 0, "company_index": 0,
        "timestamp": provenance["created_at"], "comment": provenance["comment"],
    }
    values = {
        "next_id": graph.next_persistent_id,
        "user_names": [provenance["author"]], "company_names": [provenance["company"]],
        "revision_logs": [{"object_id": graph.part["f08"], "stamps": [stamp]}],
        "created_at": provenance["created_at"], "modified_at": provenance["modified_at"],
        "updated_at": provenance["modified_at"], "component_count": 0,
        "update_stamp": 101, "body_stamp": 101, "license_flags": 0, "license_type": 0,
    }
    keyword_features = []
    for feature in features:
        item = {"id": feature["f08"], "name": feature["f18"]["f08"], "kind": feature.cls}
        if feature is extrusion.profile.profile:
            item["tag"] = "Sketch"
        if feature is extrusion.feature:
            item.update({"tag": "Extrusion", "dimensions": [{"name": "D1", "value": extrusion.depth / presentation["length_unit_m"]}]})
        keyword_features.append(item)
    configuration = graph.configuration_manager["f360"]
    return streams(
        registry=registry,
        header2=header(model_present=False, **values),
        model_headers={configuration["f08"]: header(model_present=True, **values)},
        biography_record=biography(),
        history_record=history(
            states=[{"file_version": 19000, "date_codes": [{"build_code": provenance["originating_build_code"], "native_save": False}], "stamp": stamp}],
            failure_severity=0, minimum_free_memory=0xFFFFFFFF,
            license_origin=provenance["license_origin"], language_id=presentation["language_id"],
            cjk_saved=presentation["cjk_saved"], cjk_warning=False,
        ),
        keywords_data=keywords(
            name=document["name"], timestamp=provenance["modified_at"],
            configurations=[{"id": configuration["f08"], "name": document["configuration_name"], "material": ""}],
            features=keyword_features,
        ),
    )


def construct_part(*, registry, document, provenance, presentation, target):
    document = fields(document, "part document", (
        "name", "configuration_name", "sketch_name", "extrusion_name", "origin_name",
        "plane_axis", "vertices_m", "depth_m", "density_kg_m3",
    ))
    provenance = fields(provenance, "authored provenance", (
        "author", "company", "created_at", "modified_at", "comment",
        "originating_build_code", "license_origin",
    ))
    presentation = fields(presentation, "part presentation", (
        "plane_names", "units", "styles", "hatch_name", "drafting_standard",
        "journal_name", "tessellation", "detail_flags", "system_preference_7a",
        "design_intent", "selected_leader", "cjk_saved",
    ))
    target = fields(target, "native target", ("date_code", "parasolid_version"))
    if document["plane_axis"] not in ("x", "y", "z"):
        raise ArchiveError("fresh polygon parts require a principal plane")
    styles = presentation["styles"]
    if not isinstance(styles, Mapping):
        raise ArchiveError("part styles require semantic construction parameters")
    units = presentation["units"]
    if not isinstance(units, Mapping):
        raise ArchiveError("part units require semantic construction parameters")
    length_scales = {
        "mm": 1e-3, "cm": 1e-2, "m": 1.0, "in": 0.0254, "ft": 0.3048,
        "angstrom": 1e-10, "nm": 1e-9, "um": 1e-6, "mil": 0.0000254, "microinch": 0.0000000254,
    }
    document_units = unit_table_profile(**units)
    analysis_units = unit_table_profile(length_unit="m", angle_unit="radian", unit_system="mks", decimal_places=units["decimal_places"])
    graph = part_graph(
        name=document["name"], configuration_names=(document["configuration_name"],),
        plane_names=presentation["plane_names"], detail_definitions=detail_definitions(**styles),
        document_units=document_units, analysis_units=analysis_units, hatch_name=presentation["hatch_name"],
        date_code=target["date_code"], parasolid_version=target["parasolid_version"],
        updated_at=provenance["modified_at"], retain_construction_flag=True,
    )
    plane = graph.planes[document["plane_axis"]]
    frame = PlaneFrame(origin=(0.0, 0.0, 0.0), u=plane["_plane_u"], v=plane["_plane_v"])
    reference = component_plane(
        plane=plane, component=graph.part["f990"], created_at=provenance["created_at"],
        principal_normal=tuple(plane["f6f8"]["normal"][axis] for axis in ("x", "y", "z")),
    )
    feature_values = {
        "owner": graph.part, "allocator": graph.allocator,
        "date_code": target["date_code"], "parasolid_version": target["parasolid_version"],
    }
    origin_node = model_feature(cls="moOriginProfileFeature_c", name=document["origin_name"], **feature_values)
    origin_profile(profile=origin_node, plane=reference, frame=frame)
    profile_node = model_feature(cls="moProfileFeature_c", name=document["sketch_name"], **feature_values)
    profile = closed_profile(vertices=document["vertices_m"], profile=profile_node, plane=reference, frame=frame)
    extrusion_node = body_feature(cls="moExtrusion_c", name=document["extrusion_name"], **feature_values)
    extrusion = live_blind_extrusion(
        feature=extrusion_node, profile=profile, depth=document["depth_m"], allocator=graph.allocator,
        design_intent=presentation["design_intent"], selected_leader=presentation["selected_leader"],
    )
    features = (*graph.system_features, origin_node, profile_node, extrusion_node)
    config_data, state = store_config_state(StreamDoc("config", {"direct": 0}, [graph.part]), registry, 19000)
    resolved = StreamDoc("resolved", {"base": state.count, "context": {
        "model_compressed_stream": 1, "model_is_part": 1, "cmgr_f658": graph.configuration_manager["f658"],
    }}, features)
    metadata_presentation = {
        "length_unit_m": length_scales[units["length_unit"]],
        "language_id": styles["language_id"], "cjk_saved": presentation["cjk_saved"],
    }
    result = _metadata(
        registry=registry, document=document, provenance=provenance, presentation=metadata_presentation,
        graph=graph, features=features, extrusion=extrusion,
    )
    definition = part_definition(
        density_kg_m3=document["density_kg_m3"], drafting_standard=presentation["drafting_standard"],
        detail_flags=presentation["detail_flags"], tessellation=tuple(presentation["tessellation"]),
        system_preference_7a=presentation["system_preference_7a"], journal_name=presentation["journal_name"],
    )
    result.update({
        "Contents/Config-0": config_data,
        "Contents/CMgr": _rooted(registry=registry, node=graph.configuration_manager),
        "Contents/Definition": definition_stream(registry=registry, document=definition),
        "Contents/Config-0-ResolvedFeatures": store_resolved(resolved, registry, 19000, seed=state),
    })
    return PartConstruction(
        streams=result, model=graph.part, features=features, extrusion=extrusion,
        next_id=graph.next_persistent_id, configuration_map_count=state.count,
    )
