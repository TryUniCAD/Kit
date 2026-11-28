from __future__ import annotations

import argparse
import json
from pathlib import Path, PureWindowsPath

from AssemblyMates import load_mate_list, store_mate_list
from AssemblySources import digest, require
from Classes import registry
from Core import DOCUMENT_VERSION_2026, Obj
from defs.ConfigPart import load_config
from defs.ResolvedCore import load_resolved
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Assembly.Assembly import Configurations, Files, Models, XmlRoot
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarChild, PlanarContext
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlanarMate import ReadPlanarMate
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KComponentTreeStream
from convert.adapters.solidworks.Core.Adapter import AsmInstanceId, PlaneId


ALIGNMENTS = {0: "unknown", 1: "aligned", 2: "anti_aligned"}


def read_config(archive, config_id, reg):
    version = ContainerMo(archive.streams)
    require(archive.format_version == 4 and version == DOCUMENT_VERSION_2026,
            "planar projection requires a version-19000 native archive")
    config_name = f"Contents/Config-{config_id}"
    resolved_name = config_name + "-ResolvedFeatures"
    config, config_reader = load_config(archive.require(config_name), reg, version, archive=archive, name=config_name)
    resolved, resolved_reader = load_resolved(archive.require(resolved_name), reg, version, archive=archive,
                                             name=resolved_name, seed=config_reader.map_state())
    require(not config.tail and not resolved.tail and len(config.roots) == 1,
            "the configuration graph contains unread or ambiguous records")
    return config, resolved, resolved_reader.map_state()


def read_child(archive, config_id, reg):
    config, resolved, _ = read_config(archive, config_id, reg)
    require(config.roots[0].cls == "moPart_c", "the mate endpoint must reference a part")
    datums = [node for node in resolved.roots if isinstance(node, Obj) and node.cls == "moRefPlane_c"]
    planes = {node["f08"]: node for node in datums}
    require(len(planes) == len(datums), "child datum ids are ambiguous")
    header_name = f"Contents/Config-{config_id}-ModelHeader"
    header = ReadHeaderGraph(archive.require(header_name), DOCUMENT_VERSION_2026)
    return PlanarChild(header, planes)


def assembly_index(archive):
    root = XmlRoot(archive.require(KComponentTreeStream))
    configs = Configurations(root)
    require(len(configs) == 1, "planar projection admits one assembly configuration")
    config = configs[0]
    definitions, occurrences = Models(root, {file.object_id: file for file in Files(root)})
    items = [item for item in occurrences if item.owner_definition_id == config.model_id]
    by_feature = {item.feature_id: item for item in items}
    require(len(by_feature) == len(items), "assembly occurrence feature ids are ambiguous")
    return config, by_feature, {definition.object_id: definition for definition in definitions}


def endpoint(result, order):
    return {
        "order": order,
        "occurrence_feature_id": result.OccurrenceFeatureId,
        "occurrence_object_id": result.OccurrenceObjectId,
        "instance_path": [AsmInstanceId(result.OccurrenceObjectId)],
        "child_definition_id": result.ChildDefinitionId,
        "child_configuration_id": result.ChildConfigId,
        "child_update": result.ChildUpdateStamp,
        "datum_feature_id": result.DatumFeatureId,
        "source_entity_id": PlaneId(result.DatumFeatureId),
        "datum_name": result.DatumName,
        "stored_origin_m": list(result.OriginValue),
        "stored_normal": list(result.NormalValue),
    }


def projection(assembly, child_archives):
    reg = registry()
    config, items, definitions = assembly_index(assembly)
    model_doc, _, resolved_map = read_config(assembly, config.configuration_id, reg)
    model = model_doc.roots[0]
    require(model.cls == "moAssembly_c", "planar projection requires a native assembly model")
    children = {}
    for item in items.values():
        definition = definitions[item.definition_id]
        name = PureWindowsPath(definition.source_path).name.casefold()
        key = (name, item.configuration_id)
        if name in child_archives and key not in children:
            children[key] = read_child(child_archives[name], item.configuration_id, reg)
    stream = f"Contents/Config-{config.configuration_id}-MatesList"
    raw = assembly.require(stream)
    with reg.track_usage("load", stream, sources=assembly.streams) as trace:
        mates, _ = load_mate_list(raw, reg, DOCUMENT_VERSION_2026, resolved_map=resolved_map)
    result = trace.snapshot()
    require(result["completed"] and not result["provisional_schemas"] and not result["missing_schemas"],
            "mate projection requires proven field rules")
    require(store_mate_list(mates, reg, DOCUMENT_VERSION_2026, resolved_map=resolved_map) == raw,
            "mate list round trip differs")
    context = PlanarContext(model, items, definitions, children)
    projections = []
    for mate in mates:
        result = ReadPlanarMate(context, mate, DOCUMENT_VERSION_2026)
        projections.append({
            "mate_id": result.MateId, "name": result.NameValue, "kind": result.KindValue,
            "class": result.ClassName, "alignment_code": result.AlignmentCode,
            "alignment": ALIGNMENTS[result.AlignmentCode],
            "entities": [endpoint(value, order) for order, value in enumerate(result.Endpoints)],
            "driving_distance_m": result.DistanceValue,
        })
    return {
        "version": DOCUMENT_VERSION_2026, "configuration_id": config.configuration_id,
        "mate_list_sha256": digest(raw), "mate_list_round_trip": True, "mates": projections,
    }


def read_input(path):
    data = path.read_bytes()
    return SldprtArchive.from_bytes(data, path), digest(data)


def main():
    parser = argparse.ArgumentParser(description="Project resolved planar mate identities from native archive graphs")
    parser.add_argument("assembly", type=Path)
    parser.add_argument("children", type=Path, nargs="+")
    args = parser.parse_args()
    assembly, checksum = read_input(args.assembly)
    child_names = [path.name.casefold() for path in args.children]
    require(len(set(child_names)) == len(child_names), "explicit child archive names must be unique")
    children = {name: read_input(path) for name, path in zip(child_names, args.children, strict=True)}
    result = projection(assembly, {name: value[0] for name, value in children.items()})
    print(json.dumps({
        "assembly_sha256": checksum, "child_sha256": {name: value[1] for name, value in children.items()}, **result,
    }, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
