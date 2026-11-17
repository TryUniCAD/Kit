from __future__ import annotations

import argparse
import json
from pathlib import Path, PureWindowsPath

from AssemblyMates import load_mate_list, store_mate_list
from AssemblySources import digest, require
from Classes import registry
from Core import DOCUMENT_VERSION_2026, Obj
from PlanarMateSources import MATE_CLASSES, driving_distance
from defs.ConfigPart import load_config
from defs.ResolvedCore import load_resolved
from convert.adapters.solidworks.Assembly.Assembly import Configurations, Files, Models, XmlRoot
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KComponentTreeStream
from convert.adapters.solidworks.Core.Adapter import AsmInstanceId, PlaneId


KINDS = {value: key for key, value in MATE_CLASSES.items()}
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
    return config.head["model_header"], planes


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


def occurrence_link(model, wrapper, mate, order):
    require(wrapper.cls == "moPlaneRef_w" and wrapper["f74"] == mate["f08"]
            and wrapper["f78"] == wrapper["f7c"] == order, "the resolved plane wrapper has inconsistent ownership")
    plane = wrapper["f58"]
    require(plane.cls == "moCompRefPlane_c" and plane["ff8"] is None, "resolved plane owns an unexpected target")
    chain = plane["f58"]
    require(chain.cls == "moChainComponent_c", "the resolved plane needs a component chain")
    links = chain["f20"]["f08"]["f08"]
    require(len(links) == 1 and links[0]["o"].cls == "moExtFeature_c",
            "planar projection admits a direct occurrence chain")
    link = links[0]["o"]
    reference = link["f50"]
    require(reference.cls == "moReference_c" and link["f44"] == reference["f08"] and reference["f4f8"] is link
            and any(row["o"] is reference for row in model["f68"]["list"]["items"]),
            "resolved mate plane lost its occurrence identity")
    return plane, reference


def endpoint(model, wrapper, mate, order, items, definitions, children):
    target, reference = occurrence_link(model, wrapper, mate, order)
    item = items.get(reference["f08"])
    require(item is not None and not item.suppressed, "the resolved occurrence is missing from the enabled root index")
    definition = definitions[item.definition_id]
    source_name = PureWindowsPath(definition.source_path).name.casefold()
    key = (source_name, item.configuration_id)
    require(definition.document_type == "PART" and key in children,
            "the resolved occurrence has no explicit part configuration")
    header, datums = children[key]
    selection = reference["f3c0"]
    require(wrapper["f0c"] == selection["f10"] == item.configuration_id
            and selection["f08"] == item.configuration_name, "mate wrapper child configuration differs")
    require((wrapper["f08"] & 0xffffffff) == reference["f3e0"] == header["f40"], "mate wrapper child update is stale")
    external = reference["f3b0"]["shared"]
    child_file = header["f38"]["shared"]
    require(all(external[field]["f08"] == child_file[field]["f08"] for field in ("h10", "h18")),
            "mate wrapper targets a different part identity")
    datum_id = target["ff0"]["f00"]
    require(datum_id in datums, "the real child datum is missing")
    return {
        "order": order,
        "occurrence_feature_id": reference["f08"],
        "occurrence_object_id": item.object_id,
        "instance_path": [AsmInstanceId(item.object_id)],
        "child_definition_id": item.definition_id,
        "child_configuration_id": item.configuration_id,
        "child_update": header["f40"],
        "datum_feature_id": datum_id,
        "source_entity_id": PlaneId(datum_id),
        "datum_name": datums[datum_id]["f18"]["f08"],
        "stored_origin_m": [wrapper["fd0"][axis] for axis in ("x", "y", "z")],
        "stored_normal": [wrapper["fe8"][axis] for axis in ("x", "y", "z")],
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
    projections = []
    for mate in mates:
        require(mate.cls in KINDS and mate["f3b4"] in ALIGNMENTS and len(mate["f410"]) == 2,
                "mate class, alignment or endpoint count lies outside planar projection")
        entities = [endpoint(model, row["o"], mate, order, items, definitions, children)
                    for order, row in enumerate(mate["f410"])]
        dimension = driving_distance(mate) if KINDS[mate.cls] == "distance" else None
        projections.append({
            "mate_id": mate["f08"], "name": mate["f18"]["f08"], "kind": KINDS[mate.cls], "class": mate.cls,
            "alignment_code": mate["f3b4"], "alignment": ALIGNMENTS[mate["f3b4"]], "entities": entities,
            "driving_distance_m": None if dimension is None else dimension["distance_m"],
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
