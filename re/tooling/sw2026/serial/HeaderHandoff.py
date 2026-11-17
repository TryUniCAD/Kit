from __future__ import annotations

from AssemblyMates import load_mate_list, store_mate_list
from Core import DOCUMENT_VERSION_2026, Load, Store
from defs.ConfigPart import load_config, store_config_state
from defs.ResolvedCore import load_resolved, store_resolved_state
from convert.adapters.solidworks.Archive.Header.HeaderRefNodes import HeaderRefNodes
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph


REFERENCE_CLASSES = {"moReference_c", "moReferenceInternal_c", "moReferenceBrowser_c", "moReferenceModel_c"}


def require(value, message):
    if not value:
        raise ValueError(message)


def bindings(reader, nodes, start):
    return all(reader.table[index][1] is node for index, node in enumerate(nodes, start))


def occurrence_aliases(reader, nodes):
    references = [entry[1] for entry in reader.table.values() if entry[0] == "obj"
                  and entry[1].ClassValue.NameValue in REFERENCE_CLASSES]
    require(all(any(reference.FieldsValue["f3b0"] is node for node in nodes) for reference in references),
            "an occurrence does not retain its direct header object")
    return len(references)


def inspect_handoff(archive, reg, config_name="Contents/Config-0"):
    version = DOCUMENT_VERSION_2026
    header_name = config_name + "-ModelHeader"
    header_bytes = archive.require(header_name)
    header = ReadHeaderGraph(header_bytes, version)
    nodes = HeaderRefNodes(header, version)
    source_indices = tuple(node.IndexValue for node in nodes)
    data = archive.require(config_name)
    ordinary, ordinary_reader = load_config(data, reg, version, archive=archive, name=config_name)
    require(not ordinary.tail and ordinary.roots[0].cls in ("moPart_c", "moAssembly_c"),
            "the direct handoff requires a complete ordinary part or assembly")
    source_name, source_reader = ordinary_reader.model_header_source
    require(source_name == header_name and source_reader.b == header_bytes and not source_reader.left(),
            "the ordinary header source provenance was lost")
    ordinary_bytes, ordinary_seed = store_config_state(ordinary, reg, version)
    require(ordinary_bytes == data and ordinary_reader.count == ordinary_seed.count,
            "the ordinary linked configuration did not round-trip")
    reader = Load(data, 1, reg, version, {"header_objects": nodes})
    model = reader.obj()
    require(not reader.left(), "the SDK-header configuration has unread bytes")
    writer = Store(1, reg, version, {"header_objects": nodes})
    writer.obj(model)
    require(bytes(writer.out) == data and reader.count == writer.count == ordinary_reader.count,
            "the SDK-header configuration changed bytes or allocation count")
    require(reader.base == writer.base == ordinary_reader.base, "the direct map base changed")
    direct_start = reader.base - len(nodes)
    require(bindings(ordinary_reader, ordinary_reader.ctx["header_objects"], direct_start),
            "the ordinary loader lost its original header aliases")
    require(bindings(reader, nodes, direct_start) and bindings(writer, nodes, direct_start),
            "the SDK header nodes lost their configuration slots")
    resolved_name = config_name + "-ResolvedFeatures"
    resolved_bytes = archive.require(resolved_name)
    resolved, resolved_reader = load_resolved(resolved_bytes, reg, version, archive=archive,
                                             name=resolved_name, seed=reader.map_state())
    encoded, resolved_seed = store_resolved_state(resolved, reg, version, seed=writer.map_state())
    require(not resolved.tail and encoded == resolved_bytes and resolved_reader.count == resolved_seed.count,
            "the SDK-header resolved stream changed bytes or allocation count")
    require(bindings(resolved_reader, nodes, direct_start), "the resolved graph lost direct header identities")
    mate_name = config_name + "-MatesList"
    mate_count = None
    if mate_name in archive.streams:
        mates, mate_reader = load_mate_list(archive.require(mate_name), reg, version,
                                           resolved_map=resolved_reader.map_state())
        require(store_mate_list(mates, reg, version, resolved_map=resolved_seed) == archive.require(mate_name),
                "the SDK-header mate list changed bytes")
        require(bindings(mate_reader, nodes, direct_start), "the mate graph lost direct header identities")
        mate_count = mate_reader.count
    require(tuple(node.IndexValue for node in nodes) == source_indices and WriteHeadGraph(header, version) == header_bytes,
            "direct binding mutated standalone header indices or bytes")
    return {
        "configuration": config_name, "header": header_name, "direct_count": len(nodes),
        "direct_start": direct_start, "direct_base": reader.base,
        "standalone_indices": list(source_indices), "config_map_count": reader.count,
        "resolved_map_count": resolved_reader.count, "mate_map_count": mate_count,
        "occurrence_aliases": occurrence_aliases(resolved_reader, nodes),
        "config_byte_identity": True, "resolved_byte_identity": True,
        "mate_byte_identity": None if mate_count is None else True,
        "standalone_indices_preserved": True, "direct_identity_preserved": True,
        "research_model_header_trace_retained": True,
    }
