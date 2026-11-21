from __future__ import annotations

from dataclasses import dataclass
from ntpath import normcase, normpath
from pathlib import PureWindowsPath

from Core import Obj
from Streams import StreamDoc, store_rooted
from builders.Assembly import initial_assembly_features, initial_assembly_model, initial_configuration, store_assembly_mates
from builders.AssemblyDocument import CONFIG, DEFINITION, MANAGER, MATES, RESOLVED, _child_bounds, _child_directory_entry, _header_records, _header_streams
from builders.AssemblyOccurrences import assembly_occurrence_bounds, occurrence_configuration, resolved_assembly_occurrence, resolved_part_occurrence
from builders.AssemblyTargetState import target_update_stamps
from builders.ConfigurationHeader import CONFIGURATION_MANAGER_HEADER, configuration_manager_header, configuration_manager_header_stream
from builders.DefinitionSdk import assembly_definition_stream
from builders.Metadata import FILE_VERSION, fields, integer, sequence, text
from builders.Model import PersistentIds, configuration_manager, node_list, object_list, record_configuration_progress
from builders.NestedAssemblyMetadata import nested_assembly_xml
from builders.Part import construct_part
from builders.Sketch import PlaneFrame
from builders.Styles import detail_definitions
from builders.Units import unit_table_profile
from defs.ConfigPart import store_config_state
from defs.ResolvedCore import store_resolved_state


@dataclass(frozen=True, kw_only=True)
class NestedDocument:
    streams: dict
    model: Obj
    model_header: Obj
    manager_header: Obj
    configuration: Obj
    features: tuple
    references: tuple = ()
    expanded_count: int = 0
    configuration_map_count: int = 0
    resolved_map_count: int = 0


@dataclass(frozen=True)
class NestedBundle:
    root: str
    documents: dict[str, NestedDocument]


def _assembly_request(request):
    fields(request, "nested assembly", ("name", "configuration_name", "origin_name", "mate_group_name", "provenance", "target", "presentation", "output"))
    presentation = fields(request["presentation"], "nested assembly presentation", ("styles", "units", "definition", "assembly_features", "language_id", "cjk_saved"))
    fields(request["provenance"], "nested assembly provenance", ("author", "company", "created_at", "modified_at", "comment", "originating_build_code", "license_origin"))
    fields(request["target"], "nested assembly target", ("date_code", "parasolid_version"))
    fields(request["output"], "nested assembly output", ("path_name", "saved_at"))
    return presentation


def _construct_node(*, registry, request, placements):
    presentation = _assembly_request(request)
    target, provenance = request["target"], request["provenance"]
    ids = PersistentIds()
    model = initial_assembly_model(name=request["name"], allocator=ids, detail_definitions=detail_definitions(**presentation["styles"]),
                                   document_units=unit_table_profile(**presentation["units"]))
    manager = configuration_manager(owner=model, names=[request["configuration_name"]], updated_at=provenance["modified_at"], configuration_builder=initial_configuration, **target)
    configuration = manager["f360"]
    features = initial_assembly_features(owner=model, allocator=ids, created_at=provenance["created_at"], origin_name=request["origin_name"],
                                         mate_group_name=request["mate_group_name"], **presentation["assembly_features"], **target)
    top_header, model_header, stamp = _header_records(name=request["name"], root=model, configuration=configuration, ids=ids,
                                                     provenance=provenance, output=request["output"])
    targets = {}
    for _, _, child, _ in placements:
        targets[id(child)] = child
    directory = []
    by_target = {}
    for index, (key, child) in enumerate(targets.items()):
        entry = _child_directory_entry(child=child, uses=sum(item[2] is child for item in placements))
        entry["f78"] = index
        by_target[key] = entry
        directory.append(entry)
    references = []
    for ordinal, (name, placement, child, bounds) in enumerate(placements, len(features) - 1):
        arguments = dict(owner=model, owner_file=model_header["f38"], child_model=child.model, child_header=child.model_header,
                         child_configuration=child.configuration, child_file=by_target[id(child)], name=name, placement=placement,
                         feature_ordinal=ordinal, allocator=ids, **target)
        if child.model.cls == "moPart_c":
            low, high = bounds
            reference = resolved_part_occurrence(minimum=low, maximum=high, **arguments)
        else:
            reference = resolved_assembly_occurrence(**arguments)
        references.append((reference, child))
    expanded = integer(sum(1 + child.expanded_count for _, child in references), "expanded assembly activity", high=0x7FFFFFFF)
    bounds = assembly_occurrence_bounds(occurrences=((row[0], placement[1]) for row, placement in zip(references, placements, strict=True)))
    model.f.update(has_list68=1, f68=node_list(reference for reference, _ in references), f1560=len(references),
                   has_f1a18=1, f1a18=bounds, has_f1a20=1, f1a20=dict(bounds))
    configuration["fce8"].extend({"o": occurrence_configuration(reference=reference, configuration=configuration)} for reference, _ in reversed(references))
    configuration["f4b0"] = expanded
    record_configuration_progress(configuration=configuration, allocator=ids)
    listing = Obj("moExtObjectList_c", object_list(directory))
    for header in (model_header, top_header):
        header.f.update(f08=ids.next_id, fc4=expanded, f30=listing)
    manager_header = configuration_manager_header(manager=manager, saved_at=request["output"]["saved_at"])
    streams = _header_streams(registry=registry, top_header=top_header, model_header=model_header, configuration=configuration,
                              stamp=stamp, provenance=provenance, presentation=presentation)
    config, state = store_config_state(StreamDoc(CONFIG, {"model_header": model_header}, [model]), registry, FILE_VERSION)
    context = {"model_compressed_stream": 1, "model_is_part": 0, "cmgr_f658": manager["f658"]}
    resolved, resolved_map = store_resolved_state(StreamDoc("resolved", {"base": state.count, "context": context}, features), registry, FILE_VERSION, seed=state)
    definition = dict(presentation["definition"])
    definition["tessellation"] = tuple(definition["tessellation"])
    streams.update({
        CONFIG: config,
        MANAGER: store_rooted(StreamDoc("rooted", {"base": 1}, [manager]), registry, FILE_VERSION),
        RESOLVED: resolved,
        MATES: store_assembly_mates(registry=registry, resolved_map=resolved_map, mate_group=features[-1], mates=()),
        DEFINITION: assembly_definition_stream(**definition),
        CONFIGURATION_MANAGER_HEADER: configuration_manager_header_stream(registry=registry, header=manager_header),
    })
    result = NestedDocument(streams=streams, model=model, model_header=model_header, manager_header=manager_header, configuration=configuration,
                             features=tuple(features), references=tuple(references), expanded_count=expanded,
                             configuration_map_count=state.count, resolved_map_count=resolved_map.count)
    streams.update(nested_assembly_xml(root=result))
    return result


def _native_path(request, kind):
    output = fields(request["output"], "nested document output", ("path_name", "saved_at"))
    path = PureWindowsPath(text(output["path_name"], "nested document path"))
    if not path.is_absolute() or ".." in path.parts or path.suffix.casefold() != (".sldprt" if kind == "part" else ".sldasm"):
        raise ValueError("nested documents require absolute native paths with matching extensions")
    if any(character in path.name for character in '<>:"/\\|?*') or path.name.endswith((" ", ".")):
        raise ValueError("nested document filenames must use ordinary Windows file identities")
    return normcase(normpath(str(path)))


def construct_nested_bundle(*, registry, request):
    fields(request, "nested bundle", ("root", "definitions"))
    definitions = {}
    paths = set()
    for value in sequence(request["definitions"], "nested definitions"):
        fields(value, "native definition", ("id", "kind", "request"), ("occurrences",))
        identity = text(value["id"], "definition identity")
        kind = value["kind"]
        if not identity or identity in definitions or kind not in ("part", "assembly"):
            raise ValueError("nested definitions require unique nonempty identities and native part or assembly kinds")
        if (kind == "assembly") != ("occurrences" in value):
            raise ValueError("each assembly must declare its complete direct occurrence list")
        request_path = _native_path(value["request"], kind)
        if request_path in paths:
            raise ValueError("native definitions must have distinct output paths")
        paths.add(request_path)
        definitions[identity] = value
    root = text(request["root"], "nested root identity")
    if root not in definitions or definitions[root]["kind"] != "assembly":
        raise ValueError("the nested bundle root must identify its declared native assembly")
    documents = {}
    bounds = {}
    visiting = set()

    def construct(identity):
        if identity in documents:
            return documents[identity]
        if identity in visiting or identity not in definitions:
            raise ValueError("nested occurrence graph contains a cycle or undeclared target")
        visiting.add(identity)
        definition = definitions[identity]
        if definition["kind"] == "part":
            values = fields(definition["request"], "generated nested part", ("document", "provenance", "presentation", "target", "output"))
            part = construct_part(registry=registry, native_plane_roles=True, **values)
            bounds[identity] = _child_bounds(part)
            document = NestedDocument(streams=part.streams, model=part.model, model_header=part.model_header, manager_header=part.manager_header,
                                        configuration=part.configuration, features=part.features, configuration_map_count=part.configuration_map_count)
        else:
            placements = []
            names = set()
            for item in sequence(definition["occurrences"], "nested occurrences"):
                fields(item, "nested occurrence", ("target", "name", "placement"))
                name = text(item["name"], "occurrence name")
                if name in names:
                    raise ValueError("each sibling occurrence requires its own name")
                names.add(name)
                child = construct(text(item["target"], "target definition identity"))
                placement = PlaneFrame(**fields(item["placement"], "nested occurrence placement", ("origin", "u", "v")))
                placements.append((name, placement, child, bounds.get(item["target"])))
            if not placements:
                raise ValueError("the first nested profile requires populated assembly definitions")
            document = _construct_node(registry=registry, request=definition["request"], placements=placements)
        documents[identity] = document
        visiting.remove(identity)
        return document

    construct(root)
    if set(documents) != set(definitions) or sum(value.model.cls == "moAssembly_c" for value in documents.values()) < 2:
        raise ValueError("the nested bundle requires a reachable subassembly and complete declared dependency closure")
    for document in documents.values():
        row, = document.manager_header["f08"]["items"]
        geometry, transform = target_update_stamps(document.model)
        if (row["o"]["f50"] & 0xFFFFFFFF, row["o"]["f4c"] & 0xFFFFFFFF) != (geometry, transform):
            raise ValueError("generated configuration header disagrees with its actual target stamp state")
    return NestedBundle(root, documents)
