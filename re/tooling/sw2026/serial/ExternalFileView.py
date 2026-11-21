from __future__ import annotations

from Streams import load_rooted
from defs.ConfigPart import load_config


def self_reference_fields(node):
    if node is None:
        return None
    definition = node["shared"]
    return {
        "class": node.cls,
        "path": definition["h18"]["f08"],
        "name": definition["h10"]["f08"],
        "creation_time": definition["f28"],
        "document_kind": definition["f20"],
        "configuration": node["refcfg"],
        "record": {key: node[key] for key in ("f48", "f4c", "f50", "f54", "f58", "f60", "f70", "f78")},
    }


def self_reference_summary(model_header, top_header, config_reader):
    model_self = model_header["f38"]
    fields = self_reference_fields(model_self)
    slots = [index for index, entry in config_reader.table.items() if entry[0] == "obj" and entry[1] is model_self]
    return {
        "self_reference": fields,
        "self_reference_headers_agree": fields == self_reference_fields(top_header["f38"]),
        "self_reference_direct_slots": slots,
    }


def read_self_reference(archive, registry):
    config = "Contents/Config-0"
    model_doc, config_reader = load_config(archive.require(config), registry, 19000, archive=archive, name=config)
    header_doc, header_reader = load_rooted(archive.require("Header2"), registry, 1, 19000)
    if model_doc.tail or header_doc.tail or config_reader.left() or header_reader.left():
        raise ValueError("self reference readback has unread archive bytes")
    summary = self_reference_summary(model_doc.head["model_header"], header_doc.roots[0], config_reader)
    if "Contents/CMgrHdr2" in archive.streams:
        doc, reader = load_rooted(archive.require("Contents/CMgrHdr2"), registry, 1, 19000)
        cmgr_doc, cmgr_reader = load_rooted(archive.require("Contents/CMgr"), registry, 1, 19000)
        if doc.tail or cmgr_doc.tail or reader.left() or cmgr_reader.left():
            raise ValueError("configuration manager readback has unread archive bytes")
        header, manager = doc.roots[0], cmgr_doc.roots[0]
        active = manager["f360"]
        configurations = [item["o"] for item in header["f08"]["items"]]
        summary["configuration_manager_header"] = {
            "class": header.cls,
            "saved_at": header["f60"],
            "active_configurations": [{"class": config.cls, "name": config["f10"], "id": config["f30"]} for config in configurations if config["f08"] == 1],
            "update_stamps_agree": len(configurations) == 1 and configurations[0]["f38"] == active["f860"] and configurations[0]["f50"] == model_doc.roots[0]["f1300"],
            "sort_order_agrees": header["f68"] == manager["f75c"],
        }
    return summary
