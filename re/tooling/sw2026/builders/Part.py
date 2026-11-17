from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import degrees

from Core import ArchiveError, Obj
from Streams import StreamDoc, store_rooted
from builders.Arc import open_arc_profile
from builders.Capsule import capsule_profile
from builders.Circle import circle_profile, circle_set_profile
from builders.Cut import BlindPocketGraph, blind_pocket
from builders.ConfigurationHeader import CONFIGURATION_MANAGER_HEADER, configuration_manager_header, configuration_manager_header_stream
from builders.Definition import definition_stream, part_definition
from builders.ExternalFiles import ordinary_self_reference
from builders.Extrude import DimensionGraph, live_blind_extrusion, live_extrusion
from builders.Metadata import FILE_VERSION, PRINCIPAL_KEYWORD_ROLES, biography, boolean, fields, header, history, keywords, streams
from builders.Model import body_feature, component_plane, logged_creation_time, model_feature, part_graph, record_configuration_progress
from builders.Radial import circle_dimension
from builders.RectangleAnchor import rectangle_origin
from builders.RectangleDimensions import rectangle_dimensions
from builders.ReferencePlane import OffsetPlaneGraph, construct_offset_plane
from builders.Revolve import live_revolution, revolved_profile
from builders.Sketch import PlaneFrame, closed_profile, origin_profile
from builders.Styles import detail_definitions
from builders.Units import unit_table_profile
from defs.ConfigPart import store_config_state
from defs.ResolvedCore import store_resolved


_NO_BLIND_CUT = object()
_NO_OFFSET_PLANE = object()


@dataclass(frozen=True, kw_only=True)
class PartConstruction:
    streams: dict[str, bytes]
    model: Obj
    model_header: Obj
    manager_header: Obj | None
    configuration: Obj
    features: tuple[Obj, ...]
    profile: object
    radial: object
    extrusion: object
    next_id: int
    configuration_map_count: int
    revolution: object | None = None
    rectangle_dimensions: tuple[DimensionGraph, ...] = ()
    blind_pocket: BlindPocketGraph | None = None
    offset_plane: OffsetPlaneGraph | None = None


def _rooted(*, registry, node):
    return store_rooted(StreamDoc("rooted", {"base": 1}, [node]), registry, FILE_VERSION)


def _keyword_dimensions(dimensions, length_unit_m):
    return [
        {"name": dimension.parameter["f18"]["f08"], "value": dimension.parameter["f58"] / length_unit_m}
        for dimension in dimensions
    ]


def _metadata(*, registry, document, provenance, presentation, graph, features, profile, sketch_dimensions, extrusion, output, revolution=None, native_plane_roles=False, pocket=None, offset_plane=None):
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
        plane_role = PRINCIPAL_KEYWORD_ROLES.get(feature.cls) if native_plane_roles else None
        if plane_role is not None:
            item["tag"], item["kind"] = plane_role
        if feature is profile.profile:
            item["tag"] = "Sketch"
            if revolution is not None:
                item.update(kind=None, dissectable=True)
            if sketch_dimensions:
                item["dimensions"] = _keyword_dimensions(sketch_dimensions, presentation["length_unit_m"])
        if extrusion is not None and feature is extrusion.feature:
            item.update(tag="Extrusion", dimensions=_keyword_dimensions(extrusion.active_distances, presentation["length_unit_m"]))
        if offset_plane is not None and feature is offset_plane.feature:
            item.update(tag="Feature", kind="PLANE", dimensions=_keyword_dimensions((offset_plane.distance,), presentation["length_unit_m"]))
        if pocket is not None:
            cut = pocket.extrusion
            if feature is cut.profile.profile:
                item.update(tag="Sketch", dimensions=_keyword_dimensions((pocket.radial,), presentation["length_unit_m"]))
            if feature is cut.feature:
                item.update(tag="Extrusion", kind=None, children=(cut.profile.profile["f08"],),
                            dimensions=_keyword_dimensions(cut.active_distances, presentation["length_unit_m"]))
        if revolution is not None and feature is revolution.feature:
            parameter = revolution.angle.parameter
            item.update(kind="Revolve", dimensions=[{"name": parameter["f18"]["f08"], "value": degrees(parameter["f58"]), "unit": "degree"}])
        keyword_features.append(item)
    configuration = graph.configuration_manager["f360"]
    model_header = header(model_present=True, **values)
    top_header = header(model_present=False, **values)
    if output is not None:
        own_file = ordinary_self_reference(model=graph.part, model_header=model_header, configuration=configuration, **output)
        top_header["f38"] = model_header["f38"] = own_file
    result = streams(
        registry=registry,
        header2=top_header,
        model_headers={configuration["f08"]: model_header},
        biography_record=biography(),
        history_record=history(
            states=[{"file_version": FILE_VERSION, "date_codes": [{"build_code": provenance["originating_build_code"], "native_save": False}], "stamp": stamp}],
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
    return result, model_header


def document_shape(document):
    if not isinstance(document, Mapping):
        raise ArchiveError("part document must be a semantic mapping")
    profile_kind = document.get("profile_kind", "polygon")
    feature_kind = document.get("feature_kind", "blind_extrusion")
    if profile_kind not in ("polygon", "circle", "circle_set", "arc", "capsule") or feature_kind not in ("sketch", "blind_extrusion", "extrusion", "revolve"):
        raise ArchiveError("unsupported fresh profile or feature kind")
    if feature_kind == "revolve" and profile_kind != "polygon":
        raise ArchiveError("this revolve candidate requires a closed rectangular contour")
    if profile_kind in ("circle_set", "arc") and feature_kind != "sketch":
        raise ArchiveError("this curve profile admits only the free sketch research rung")
    if profile_kind == "circle" and feature_kind in ("blind_extrusion", "extrusion"):
        request = document.get("circle_dimension")
        if not isinstance(request, Mapping) or request.get("fix_center") is not True:
            raise ArchiveError("circle extrusion requires an explicit driving dimension and fixed center")
    required = (
        "name", "configuration_name", "sketch_name", "origin_name",
        "plane_axis", "density_kg_m3",
    )
    if feature_kind == "revolve":
        required += ("revolution_name", "axis_start_m", "axis_end_m", "angle_rad", "reverse_direction")
    else:
        required += ("extrusion_name",)
    required += {"polygon": ("vertices_m",), "circle": ("center_m", "radius_m"), "circle_set": ("circles_m",), "arc": ("center_m", "radius_m", "start_angle_rad", "sweep_angle_rad"), "capsule": ("center_m", "radius_m", "straight_length_m", "rotation_angle_rad")}[profile_kind]
    if feature_kind in ("blind_extrusion", "extrusion"):
        required += ("depth_m",)
    if feature_kind == "extrusion":
        required += ("end_condition", "reverse_direction")
        if document.get("end_condition") == "two_directions":
            required += ("reverse_depth_m",)
    optional = ("profile_kind", "feature_kind") + (("circle_dimension",) if profile_kind == "circle" else ())
    if profile_kind == "polygon" and feature_kind in ("sketch", "blind_extrusion"):
        optional += ("rectangle_dimensions",)
    return fields(document, "part document", required, optional), profile_kind, feature_kind


def construct_part(*, registry, document, provenance, presentation, target, output=None, native_plane_roles: bool = False, blind_cut_discovery=_NO_BLIND_CUT, offset_plane_discovery=_NO_OFFSET_PLANE, rectangle_anchor=None):
    boolean(native_plane_roles, "native plane keyword roles")
    document, profile_kind, feature_kind = document_shape(document)
    if rectangle_anchor is not None and (rectangle_anchor not in ("corner", "center") or profile_kind != "polygon" or
        feature_kind != "blind_extrusion" or document["plane_axis"] != "z" or "rectangle_dimensions" not in document or
        blind_cut_discovery is not _NO_BLIND_CUT or offset_plane_discovery is not _NO_OFFSET_PLANE):
        raise ArchiveError("rectangle anchor discovery requires one origin-anchored dimensioned Front Plane blind boss")
    if blind_cut_discovery is not _NO_BLIND_CUT and (profile_kind != "polygon" or feature_kind != "blind_extrusion" or document["plane_axis"] != "z" or native_plane_roles):
        raise ArchiveError("blind cut discovery requires a standalone Front Plane part with one ordinary rectangular blind boss")
    if offset_plane_discovery is not _NO_OFFSET_PLANE:
        if profile_kind != "circle" or feature_kind != "blind_extrusion" or blind_cut_discovery is not _NO_BLIND_CUT or tuple(document["center_m"]) != (0.0, 0.0) or document["circle_dimension"].get("mode") != "radius":
            raise ArchiveError("offset-plane discovery requires a centered driving circle and one blind boss")
    provenance = fields(provenance, "authored provenance", (
        "author", "company", "created_at", "modified_at", "comment",
        "originating_build_code", "license_origin",
    ))
    presentation = fields(presentation, "part presentation", (
        "plane_names", "units", "styles", "hatch_name", "drafting_standard",
        "journal_name", "tessellation", "detail_flags", "system_preference_7a",
        "design_intent", "selected_leader", "cjk_saved",
        "folder_names", "cabinet_name",
    ), ("folder_order",))
    target = fields(target, "native target", ("date_code", "parasolid_version"))
    if output is not None:
        output = fields(output, "part output", ("path_name", "saved_at"))
    if document["plane_axis"] not in ("x", "y", "z"):
        raise ArchiveError("fresh research parts require a principal plane")
    if offset_plane_discovery is not _NO_OFFSET_PLANE:
        plane_request = fields(offset_plane_discovery, "ordinary offset-plane discovery", ("name", "distance_m", "reverse"))
        existing_names = (*presentation["plane_names"].values(), *presentation["folder_names"].values(), presentation["cabinet_name"],
                          document["name"], document["sketch_name"], document["extrusion_name"], document["origin_name"])
        if plane_request["name"] in existing_names:
            raise ArchiveError("the authored offset plane must have its own distinct feature name")
    styles = presentation["styles"]
    if not isinstance(styles, Mapping):
        raise ArchiveError("part styles require semantic construction parameters")
    units = presentation["units"]
    if not isinstance(units, Mapping):
        raise ArchiveError("part units require semantic construction parameters")
    if feature_kind == "revolve" and units.get("angle_unit") != "degree":
        raise ArchiveError("the ordinary revolve metadata candidate requires degree presentation")
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
        folder_order=presentation.get("folder_order"),
    )
    plane = graph.planes[document["plane_axis"]]
    feature_values = {
        "owner": graph.part, "allocator": graph.allocator,
        "date_code": target["date_code"], "parasolid_version": target["parasolid_version"],
    }
    origin_node = model_feature(cls="moOriginProfileFeature_c", name=document["origin_name"], **feature_values)
    offset_plane = None
    if offset_plane_discovery is not _NO_OFFSET_PLANE:
        offset_plane = construct_offset_plane(
            request=offset_plane_discovery, support=plane, owner=graph.part, allocator=graph.allocator,
            date_code=target["date_code"], parasolid_version=target["parasolid_version"],
            created_at=logged_creation_time(timestamps=()), design_intent=presentation["design_intent"],
            selected_leader=presentation["selected_leader"],
        )
        plane = offset_plane.feature
    frame = offset_plane.frame if offset_plane is not None else PlaneFrame(origin=(0.0, 0.0, 0.0), u=plane["_plane_u"], v=plane["_plane_v"])
    reference_values = {
        "plane": plane, "component": graph.part["f990"],
        "created_at": logged_creation_time(timestamps=()),
        "principal_normal": None if offset_plane is not None else tuple(plane["f6f8"]["normal"][axis] for axis in ("x", "y", "z")),
    }
    if offset_plane is None:
        origin_graph = origin_profile(profile=origin_node, plane=component_plane(**reference_values), frame=frame)
    else:
        support = offset_plane.support
        origin_frame = PlaneFrame(origin=(0.0, 0.0, 0.0), u=support["_plane_u"], v=support["_plane_v"])
        origin_reference = {**reference_values, "plane": support, "principal_normal": origin_frame.normal}
        origin_graph = origin_profile(profile=origin_node, plane=component_plane(**origin_reference), frame=origin_frame)
    profile_node = model_feature(cls="moProfileFeature_c", name=document["sketch_name"], **feature_values)
    revolve_source = None
    if feature_kind == "revolve":
        revolve_source = revolved_profile(vertices=document["vertices_m"], axis_start=document["axis_start_m"], axis_end=document["axis_end_m"], profile=profile_node, plane=component_plane(**reference_values), frame=frame)
        profile = revolve_source.profile
    elif profile_kind == "polygon":
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
            offset_plane=offset_plane,
        )
    rectangle = ()
    if "rectangle_dimensions" in document:
        request = fields(document["rectangle_dimensions"], "rectangle dimensions", ("width_text_m", "height_text_m", "route_centerline"))
        rectangle = rectangle_dimensions(
            graph=profile, allocator=graph.allocator, **request,
            design_intent=presentation["design_intent"], selected_leader=presentation["selected_leader"],
        )
    features = (*graph.system_features, origin_node, *((offset_plane.feature,) if offset_plane is not None else ()), profile_node)
    extrusion = None
    revolution = None
    if feature_kind in ("blind_extrusion", "extrusion"):
        extrusion_node = body_feature(cls="moExtrusion_c", name=document["extrusion_name"], **feature_values)
        if feature_kind == "blind_extrusion":
            extrusion = live_blind_extrusion(
                feature=extrusion_node, profile=profile, depth=document["depth_m"], allocator=graph.allocator,
                design_intent=presentation["design_intent"], selected_leader=presentation["selected_leader"],
            )
        else:
            extrusion = live_extrusion(
                feature=extrusion_node, profile=profile, depth=document["depth_m"], allocator=graph.allocator,
                design_intent=presentation["design_intent"], selected_leader=presentation["selected_leader"],
                condition=document["end_condition"], reverse_direction=document["reverse_direction"],
                reverse_depth=document.get("reverse_depth_m"),
            )
        features += (extrusion_node,)
    elif revolve_source is not None:
        revolve_node = body_feature(cls="moRevolution_c", name=document["revolution_name"], **feature_values)
        revolution = live_revolution(
            feature=revolve_node, source=revolve_source, allocator=graph.allocator, component=graph.part["f990"],
            profile_created_at=logged_creation_time(timestamps=()), angle_rad=document["angle_rad"], reverse_direction=document["reverse_direction"],
            design_intent=presentation["design_intent"], selected_leader=presentation["selected_leader"],
        )
        features += (revolve_node,)
    if rectangle_anchor is not None:
        rectangle_origin(graph=profile, origin=origin_graph, component=graph.part["f990"], mode=rectangle_anchor,
                         origin_created_at=logged_creation_time(timestamps=()))
    pocket = None
    if blind_cut_discovery is not _NO_BLIND_CUT:
        pocket = blind_pocket(
            request=blind_cut_discovery, boss=extrusion, feature_values=feature_values,
            reference_values=reference_values, features=features,
            design_intent=presentation["design_intent"], selected_leader=presentation["selected_leader"],
        )
        features += (pocket.extrusion.profile.profile, pocket.extrusion.feature)
    record_configuration_progress(configuration=graph.configuration_manager["f360"], allocator=graph.allocator)
    metadata_presentation = {
        "length_unit_m": length_scales[units["length_unit"]],
        "language_id": styles["language_id"], "cjk_saved": presentation["cjk_saved"],
    }
    result, model_header = _metadata(
        registry=registry, document=document, provenance=provenance, presentation=metadata_presentation,
        graph=graph, features=features, profile=profile, sketch_dimensions=(radial,) if radial is not None else rectangle,
        extrusion=extrusion, output=output, revolution=revolution, native_plane_roles=native_plane_roles, pocket=pocket, offset_plane=offset_plane,
    )
    config_data, state = store_config_state(StreamDoc("config", {"model_header": model_header}, [graph.part]), registry, FILE_VERSION)
    resolved = StreamDoc("resolved", {"base": state.count, "context": {
        "model_compressed_stream": 1, "model_is_part": 1, "cmgr_f658": graph.configuration_manager["f658"],
    }}, features)
    definition = part_definition(
        density_kg_m3=document["density_kg_m3"], drafting_standard=presentation["drafting_standard"],
        detail_flags=presentation["detail_flags"], tessellation=tuple(presentation["tessellation"]),
        system_preference_7a=presentation["system_preference_7a"], journal_name=presentation["journal_name"],
    )
    result.update({
        "Contents/Config-0": config_data,
        "Contents/CMgr": _rooted(registry=registry, node=graph.configuration_manager),
        "Contents/Definition": definition_stream(registry=registry, document=definition),
        "Contents/Config-0-ResolvedFeatures": store_resolved(resolved, registry, FILE_VERSION, seed=state),
    })
    manager_header = None
    if output is not None:
        manager_header = configuration_manager_header(manager=graph.configuration_manager, saved_at=output["saved_at"])
        result[CONFIGURATION_MANAGER_HEADER] = configuration_manager_header_stream(registry=registry, header=manager_header)
    return PartConstruction(
        streams=result, model=graph.part, model_header=model_header, manager_header=manager_header,
        configuration=graph.configuration_manager["f360"], features=features,
        profile=profile, radial=radial, extrusion=extrusion,
        next_id=graph.next_persistent_id, configuration_map_count=state.count,
        revolution=revolution, rectangle_dimensions=rectangle, blind_pocket=pocket, offset_plane=offset_plane,
    )
