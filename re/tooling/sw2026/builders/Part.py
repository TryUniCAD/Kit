from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from Core import ArchiveError, Obj
from Streams import StreamDoc, store_rooted
from builders.Arc import open_arc_profile
from builders.Capsule import capsule_profile
from builders.Circle import circle_profile, circle_set_profile
from builders.Definition import definition_stream, part_definition
from builders.Extrude import live_blind_extrusion
from builders.Metadata import biography, fields, header, history, keywords, streams
from builders.Model import body_feature, component_plane, logged_creation_time, model_feature, part_graph, record_configuration_progress
from builders.Radial import circle_dimension
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
    profile: object
    radial: object
    extrusion: object
    next_id: int
    configuration_map_count: int


def _rooted(*, registry, node):
    return store_rooted(StreamDoc("rooted", {"base": 1}, [node]), registry, 19000)


def _metadata(*, registry, document, provenance, presentation, graph, features, profile, radial, extrusion):
    stamp = {
        "status": 0, "user_index": 0, "company_index": 0,
        "timestamp": provenance["created_at"], "comment": provenance["comment"],
    }
    values = {
        "next_id": graph.next_persistent_id,
        "user_names": [provenance["author"]], "company_names": [provenance["company"]],
        "revision_logs": [{"object_id": graph.part["f08"], "name": document["name"], "stamps": [stamp]}],
        "created_at": provenance["created_at"], "modified_at": provenance["modified_at"],
        "updated_at": provenance["modified_at"], "component_count": 0,
        "update_stamp": 101, "body_stamp": 101, "license_flags": 0, "license_type": 0,
    }
    keyword_features = []
    for feature in features:
        item = {"id": feature["f08"], "name": feature["f18"]["f08"], "kind": feature.cls}
        if feature is profile.profile:
            item["tag"] = "Sketch"
            if radial is not None:
                item["dimensions"] = [{"name": radial.parameter["f18"]["f08"], "value": radial.parameter["f58"] / presentation["length_unit_m"]}]
        if extrusion is not None and feature is extrusion.feature:
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


def document_shape(document):
    if not isinstance(document, Mapping):
        raise ArchiveError("part document must be a semantic mapping")
    profile_kind = document.get("profile_kind", "polygon")
    feature_kind = document.get("feature_kind", "blind_extrusion")
    if profile_kind not in ("polygon", "circle", "circle_set", "arc", "capsule") or feature_kind not in ("sketch", "blind_extrusion"):
        raise ArchiveError("unsupported fresh profile or feature kind")
    if profile_kind in ("circle_set", "arc", "capsule") and feature_kind != "sketch":
        raise ArchiveError("this curve profile admits only the free sketch research rung")
    if profile_kind == "circle" and feature_kind == "blind_extrusion":
        request = document.get("circle_dimension")
        if not isinstance(request, Mapping) or request.get("fix_center") is not True:
            raise ArchiveError("circle extrusion requires an explicit driving dimension and fixed center")
    required = (
        "name", "configuration_name", "sketch_name", "extrusion_name", "origin_name",
        "plane_axis", "density_kg_m3",
    )
    required += {"polygon": ("vertices_m",), "circle": ("center_m", "radius_m"), "circle_set": ("circles_m",), "arc": ("center_m", "radius_m", "start_angle_rad", "sweep_angle_rad"), "capsule": ("center_m", "radius_m", "straight_length_m", "rotation_angle_rad")}[profile_kind]
    if feature_kind == "blind_extrusion":
        required += ("depth_m",)
    optional = ("profile_kind", "feature_kind") + (("circle_dimension",) if profile_kind == "circle" else ())
    return fields(document, "part document", required, optional), profile_kind, feature_kind


def construct_part(*, registry, document, provenance, presentation, target):
    document, profile_kind, feature_kind = document_shape(document)
    provenance = fields(provenance, "authored provenance", (
        "author", "company", "created_at", "modified_at", "comment",
        "originating_build_code", "license_origin",
    ))
    presentation = fields(presentation, "part presentation", (
        "plane_names", "units", "styles", "hatch_name", "drafting_standard",
        "journal_name", "tessellation", "detail_flags", "system_preference_7a",
        "design_intent", "selected_leader", "cjk_saved",
        "folder_names", "cabinet_name",
    ))
    target = fields(target, "native target", ("date_code", "parasolid_version"))
    if document["plane_axis"] not in ("x", "y", "z"):
        raise ArchiveError("fresh research parts require a principal plane")
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
        folder_names=presentation["folder_names"], cabinet_name=presentation["cabinet_name"],
        document_units=document_units, analysis_units=analysis_units, hatch_name=presentation["hatch_name"],
        date_code=target["date_code"], parasolid_version=target["parasolid_version"],
        updated_at=provenance["modified_at"], created_at=provenance["created_at"], retain_construction_flag=True,
    )
    plane = graph.planes[document["plane_axis"]]
    frame = PlaneFrame(origin=(0.0, 0.0, 0.0), u=plane["_plane_u"], v=plane["_plane_v"])
    reference_values = {
        "plane": plane, "component": graph.part["f990"],
        "created_at": logged_creation_time(timestamps=()),
        "principal_normal": tuple(plane["f6f8"]["normal"][axis] for axis in ("x", "y", "z")),
    }
    feature_values = {
        "owner": graph.part, "allocator": graph.allocator,
        "date_code": target["date_code"], "parasolid_version": target["parasolid_version"],
    }
    origin_node = model_feature(cls="moOriginProfileFeature_c", name=document["origin_name"], **feature_values)
    origin_profile(profile=origin_node, plane=component_plane(**reference_values), frame=frame)
    profile_node = model_feature(cls="moProfileFeature_c", name=document["sketch_name"], **feature_values)
    if profile_kind == "polygon":
        profile = closed_profile(vertices=document["vertices_m"], profile=profile_node, plane=component_plane(**reference_values), frame=frame)
    elif profile_kind == "circle":
        profile = circle_profile(center_m=document["center_m"], radius_m=document["radius_m"], profile=profile_node, plane=component_plane(**reference_values), frame=frame)
    elif profile_kind == "circle_set":
        profile = circle_set_profile(circles_m=document["circles_m"], profile=profile_node, plane=component_plane(**reference_values), frame=frame)
    elif profile_kind == "arc":
        profile = open_arc_profile(center_m=document["center_m"], radius_m=document["radius_m"], start_angle_rad=document["start_angle_rad"], sweep_angle_rad=document["sweep_angle_rad"], profile=profile_node, plane=component_plane(**reference_values), frame=frame)
    else:
        profile = capsule_profile(center_m=document["center_m"], radius_m=document["radius_m"], straight_length_m=document["straight_length_m"], rotation_angle_rad=document["rotation_angle_rad"], profile=profile_node, plane=component_plane(**reference_values), frame=frame)
    radial = None
    if "circle_dimension" in document:
        request = fields(document["circle_dimension"], "circle dimension", ("mode", "text_point_m"), ("fix_center",))
        radial = circle_dimension(
            graph=profile, allocator=graph.allocator, **request,
            design_intent=presentation["design_intent"], selected_leader=presentation["selected_leader"],
        )
    features = (*graph.system_features, origin_node, profile_node)
    extrusion = None
    if feature_kind == "blind_extrusion":
        extrusion_node = body_feature(cls="moExtrusion_c", name=document["extrusion_name"], **feature_values)
        extrusion = live_blind_extrusion(
            feature=extrusion_node, profile=profile, depth=document["depth_m"], allocator=graph.allocator,
            design_intent=presentation["design_intent"], selected_leader=presentation["selected_leader"],
        )
        features += (extrusion_node,)
    record_configuration_progress(configuration=graph.configuration_manager["f360"], allocator=graph.allocator)
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
        graph=graph, features=features, profile=profile, radial=radial, extrusion=extrusion,
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
        streams=result, model=graph.part, features=features, profile=profile, radial=radial, extrusion=extrusion,
        next_id=graph.next_persistent_id, configuration_map_count=state.count,
    )
