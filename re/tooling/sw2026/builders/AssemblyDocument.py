from __future__ import annotations

from dataclasses import dataclass
from ntpath import normcase, normpath

from Core import Obj
from Streams import StreamDoc, store_rooted
from builders.Assembly import initial_assembly_features, initial_assembly_model, initial_configuration, store_assembly_mates
from builders.AssemblyMetadata import assembly_xml_streams
from builders.AssemblyOccurrences import assembly_occurrence_bounds, occurrence_configuration, resolved_part_occurrence
from builders.AssemblyPlanarMate import aligned_planar_mate
from builders.DefinitionSdk import assembly_definition_stream
from builders.ExternalFiles import ordinary_self_reference, referenced_configuration
from builders.Metadata import BIOGRAPHY_STREAM, FILE_VERSION, HISTORY_STREAM, biography, boolean, fields, header, history, revision_log, rooted_metadata_streams, semantic_stamp, sequence
from builders.Model import PersistentIds, configuration_manager, node_list, object_list, record_configuration_progress
from builders.Part import PartConstruction, construct_part
from builders.Sketch import PlaneFrame
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
METADATA = ("Header2", MODEL_HEADER, BIOGRAPHY_STREAM, HISTORY_STREAM)


@dataclass(frozen=True)
class AssemblyConstruction:
    streams: dict[str, bytes]
    config_map_count: int
    resolved_map_count: int


@dataclass(frozen=True)
class AssemblyBundle:
    assembly: AssemblyConstruction
    child: PartConstruction


def _header_records(*, name, root, configuration, ids, provenance, output):
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
    top_header = header(model_present=False, **values)
    if output is not None:
        own_file = ordinary_self_reference(model=root, model_header=model_header, configuration=configuration, **output)
        top_header["f38"] = model_header["f38"] = own_file
    return top_header, model_header, stamp


def _header_streams(*, registry, top_header, model_header, configuration, stamp, provenance, presentation):
    return rooted_metadata_streams(
        registry=registry, header2=top_header,
        model_headers={configuration["f08"]: model_header},
        biography_record=biography(),
        history_record=history(
            states=[{"file_version": FILE_VERSION, "date_codes": [{"build_code": provenance["originating_build_code"], "native_save": False}], "stamp": stamp}],
            failure_severity=0, minimum_free_memory=0xFFFFFFFF,
            license_origin=provenance["license_origin"], language_id=presentation["language_id"],
            cjk_saved=presentation["cjk_saved"], cjk_warning=False,
        ),
    )


def _child_bounds(child: PartConstruction) -> tuple[tuple[float, ...], tuple[float, ...]]:
    extrusion = child.extrusion
    profile = child.profile
    if extrusion is None or extrusion.condition != "blind" or extrusion.reverse_direction or profile.arc_count or profile.line_count < 3:
        raise ValueError("the generated child must have a forward blind polygon extrusion")
    frame = profile.profile["_frame"]
    base = tuple(frame.world_point(point=(node["pos"]["x"], node["pos"]["y"])) for node in profile.points)
    extruded = tuple(tuple(value + extrusion.depth * direction for value, direction in zip(point, frame.normal, strict=True)) for point in base)
    coordinates = tuple(zip(*base, *extruded, strict=True))
    return tuple(min(axis) for axis in coordinates), tuple(max(axis) for axis in coordinates)


def _child_directory_entry(*, child: PartConstruction, uses: int) -> Obj:
    child_file = child.model_header["f38"]
    if child_file is None or child.manager_header is None:
        raise ValueError("the generated child must have its own file and configuration-manager headers")
    return Obj("moExtObject_c", {
        "shared": dict(child_file["shared"]),
        "f48": uses,
        "f4c": 0,
        "f50": 0,
        "f54": 0,
        "f58": 0,
        "f60": child_file["f60"],
        "f70": child.manager_header["f60"],
        "f78": 0,
        "refcfg": referenced_configuration(name=None, local_id=None),
    })


def _insert_generated_child(*, model, configuration, top_header, model_header, child, occurrences, ids, target, first_ordinal):
    owner_file = model_header["f38"]
    if owner_file is None:
        raise ValueError("an assembly with occurrences requires an explicit native output path")
    count = len(occurrences)
    directory_entry = _child_directory_entry(child=child, uses=count)
    parent_path, child_path = (record["shared"]["h18"]["f08"] for record in (owner_file, directory_entry))
    if normcase(normpath(parent_path)) == normcase(normpath(child_path)):
        raise ValueError("the assembly and generated child must have separate paths")
    minimum, maximum = _child_bounds(child)
    references = tuple(
        resolved_part_occurrence(
            owner=model, owner_file=owner_file, child_model=child.model, child_header=child.model_header,
            child_configuration=child.configuration, child_file=directory_entry, name=name,
            placement=placement, minimum=minimum, maximum=maximum, feature_ordinal=ordinal,
            allocator=ids, **target,
        )
        for ordinal, (name, placement) in enumerate(occurrences, first_ordinal)
    )
    bounds = assembly_occurrence_bounds(occurrences=zip(references, (placement for _, placement in occurrences), strict=True))
    model.f.update(has_list68=1, f68=node_list(references), f1560=count, has_f1a18=1, f1a18=bounds, has_f1a20=1, f1a20=dict(bounds))
    configuration["fce8"].extend({"o": occurrence_configuration(reference=reference, configuration=configuration)} for reference in reversed(references))
    configuration["f4b0"] = count
    record_configuration_progress(configuration=configuration, allocator=ids)
    directory = Obj("moExtObjectList_c", object_list((directory_entry,)))
    for record in (top_header, model_header):
        record.f.update(f08=ids.next_id, fc4=count, f30=directory)
    return references


def _record_mate_creation(*, mate, allocator, configuration, headers, stamp):
    record_configuration_progress(configuration=configuration, allocator=allocator)
    name = mate["f18"]["f08"]
    entry = semantic_stamp(stamp)
    for record in headers:
        logs = record["f20"]
        logs["items"].append({"o": revision_log(object_id=mate["f08"], name=name, entries=[dict(entry)])})
        logs["n"] = len(logs["items"])
        record["f08"] = allocator.next_id


def _construct_assembly(*, registry, request, child=None, occurrences=(), mate_requests=(), include_xml_metadata: bool = False) -> AssemblyConstruction:
    boolean(include_xml_metadata, "assembly XML metadata")
    if type(include_xml_metadata) is not bool:
        raise ValueError("assembly XML metadata selection must be boolean")
    fields(request, "assembly", ("name", "configuration_name", "origin_name", "mate_group_name", "provenance", "target", "presentation"), ("output",))
    name, presentation, provenance = (request[key] for key in ("name", "presentation", "provenance"))
    dimension_fields = ("design_intent", "selected_leader") if mate_requests and mate_requests[0].get("kind") == "distance" else ()
    fields(presentation, "assembly presentation", ("styles", "units", "definition", "assembly_features", "language_id", "cjk_saved", *dimension_fields))
    fields(provenance, "assembly provenance", ("author", "company", "created_at", "modified_at", "comment", "originating_build_code", "license_origin"))
    target = fields(request["target"], "assembly target", ("date_code", "parasolid_version"))
    output = fields(request["output"], "assembly output", ("path_name", "saved_at")) if "output" in request else None
    ids = PersistentIds()
    model = initial_assembly_model(name=name, allocator=ids, detail_definitions=detail_definitions(**presentation["styles"]), document_units=unit_table_profile(**presentation["units"]))
    manager = configuration_manager(owner=model, names=[request["configuration_name"]], updated_at=provenance["modified_at"], configuration_builder=initial_configuration, **target)
    features = initial_assembly_features(owner=model, allocator=ids, created_at=provenance["created_at"], origin_name=request["origin_name"], mate_group_name=request["mate_group_name"], **presentation["assembly_features"], **target)
    configuration = manager["f360"]
    top_header, model_header, stamp = _header_records(name=name, root=model, configuration=configuration, ids=ids, provenance=provenance, output=output)
    mates = ()
    if child is not None:
        references = _insert_generated_child(
            model=model, configuration=configuration, top_header=top_header, model_header=model_header,
            child=child, occurrences=occurrences, ids=ids, target=target, first_ordinal=len(features) - 1,
        )
        if mate_requests:
            mate_request, = mate_requests
            created_at = mate_request.get("created_at", provenance["modified_at"])
            mate = aligned_planar_mate(
                assembly=model, group=features[-1], occurrences=references, child=child, model_header=model_header,
                configuration=configuration, allocator=ids, target=target, request=mate_request, created_at=created_at,
                dimension_presentation={key: presentation[key] for key in dimension_fields},
            )
            _record_mate_creation(mate=mate, allocator=ids, configuration=configuration, headers=(top_header, model_header),
                                  stamp={**stamp, "timestamp": created_at})
            mates = (mate,)
    result = _header_streams(registry=registry, top_header=top_header, model_header=model_header, configuration=configuration, stamp=stamp, provenance=provenance, presentation=presentation)
    config, state = store_config_state(StreamDoc(CONFIG, {"model_header": model_header}, [model]), registry, FILE_VERSION)
    context = {"model_compressed_stream": 1, "model_is_part": 0, "cmgr_f658": manager["f658"]}
    resolved, final_map = store_resolved_state(StreamDoc("resolved", {"base": state.count, "context": context}, features), registry, FILE_VERSION, seed=state)
    options = dict(presentation["definition"])
    options["tessellation"] = tuple(options["tessellation"])
    result.update({
        CONFIG: config,
        MANAGER: store_rooted(StreamDoc("rooted", {"base": 1}, [manager]), registry, FILE_VERSION),
        RESOLVED: resolved,
        MATES: store_assembly_mates(registry=registry, resolved_map=final_map, mate_group=features[-1], mates=mates),
        DEFINITION: assembly_definition_stream(**options),
    })
    if include_xml_metadata:
        result.update(assembly_xml_streams(model=model, configuration=configuration, model_header=model_header, features=features, child=child))
    return AssemblyConstruction(result, state.count, final_map.count)


def construct_empty_assembly(*, registry, request, include_xml_metadata: bool = False) -> AssemblyConstruction:
    return _construct_assembly(registry=registry, request=request, include_xml_metadata=include_xml_metadata)


def construct_assembly_bundle(*, registry, request, include_xml_metadata: bool = False) -> AssemblyBundle:
    values = fields(request, "generated assembly bundle", ("assembly", "child", "occurrences"), ("mates",))
    occurrences = []
    for item in sequence(values["occurrences"], "assembly occurrences"):
        occurrence = fields(item, "assembly occurrence", ("name", "placement"))
        frame = fields(occurrence["placement"], "occurrence placement", ("origin", "u", "v"))
        occurrences.append((occurrence["name"], PlaneFrame(**frame)))
    if not occurrences:
        raise ValueError("this research bundle requires at least one resolved occurrence")
    mates = tuple(sequence(values.get("mates", ()), "assembly mates"))
    if len(mates) > 1 or any(not isinstance(mate, dict) for mate in mates):
        raise ValueError("the discovery composer accepts a single supported planar mate")
    child_request = fields(values["child"], "generated child", ("document", "provenance", "presentation", "target", "output"))
    child = construct_part(registry=registry, native_plane_roles=include_xml_metadata, **child_request)
    return AssemblyBundle(_construct_assembly(registry=registry, request=values["assembly"], child=child, occurrences=occurrences,
                                              mate_requests=mates, include_xml_metadata=include_xml_metadata), child)
