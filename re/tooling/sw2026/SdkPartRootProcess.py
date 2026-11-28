from __future__ import annotations

from base64 import b64encode
from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026"), str(ROOT / "re/tooling/sw2026/serial")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from Classes import registry
from builders.HeaderGraphBridge import generated_header_bytes
from builders.Metadata import header
from builders.Styles import detail_definitions
from builders.Units import unit_table_profile
from builders.Views import standard_views
from builders.Visual import model_visual_properties
from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigSpec import ConfigSpec
from convert.adapters.solidworks.Archive.Construction.Configuration.MakePartConfig import MakePartConfig
from convert.adapters.solidworks.Archive.Construction.Files.MakeSelfFile import MakeSelfFile
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Model.MakePartRootMut import MakePartRootMut
from convert.adapters.solidworks.Archive.Construction.Model.PartRootInput import PartRootInput
from convert.adapters.solidworks.Archive.Construction.Model.PartRootRefs import PartRootRefs
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import FeatureTarget
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass

REGISTRY = registry()
CODECS = tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def require(value, message):
    if not value:
        raise ValueError(message)


def reject(operation, label):
    try:
        operation()
    except (ValueError, TypeError, KeyError) as error:
        return {"case": label, "rejected": True, "exception": type(error).__name__, "diagnostic": str(error)}
    raise ValueError(f"malformed part root construction was accepted: {label}")


def malformed(inputs, refs, allocator):
    invalid = [reject(lambda: PartRootInput("", inputs.HatchName, 19000), "empty_model_name"),
               reject(lambda: PartRootInput(inputs.NameValue, "a\x00b", 19000), "null_hatch_name"),
               reject(lambda: PartRootInput(inputs.NameValue, inputs.HatchName, 18999), "unsupported_version"),
               reject(lambda: PartRootInput(inputs.NameValue, inputs.HatchName, True), "boolean_version"),
               reject(lambda: MakePartRootMut(inputs, refs, None), "missing_allocator")]
    bindings = (refs.DetailFields, refs.DocumentUnits, refs.AnalysisUnits, refs.VisualValue, refs.ViewValues)
    invalid.append(reject(lambda: MakePartRootMut(inputs, PartRootRefs(bindings[0], bindings[1], bindings[1], bindings[3], bindings[4]), allocator), "aliased_unit_owners"))
    invalid.append(reject(lambda: MakePartRootMut(inputs, PartRootRefs(*bindings[:4], bindings[4][:-1]), allocator), "missing_view"))
    invalid.append(reject(lambda: MakePartRootMut(inputs, PartRootRefs(*bindings[:4], (bindings[4][0],) * 10), allocator), "aliased_view_owners"))
    alternate_details = dict(refs.DetailFields)
    alternate_details["f10"] = 0
    invalid.append(reject(lambda: MakePartRootMut(inputs, PartRootRefs(alternate_details, *bindings[1:]), allocator), "unsupported_detail_standard"))
    placeholder = ArchiveNode(ExternalClass("moUnitsTable_c", 1), {})
    invalid.append(reject(lambda: MakePartRootMut(inputs, PartRootRefs(bindings[0], placeholder, *bindings[2:]), allocator), "external_unit_class_placeholder"))
    return invalid


def main():
    details = detail_definitions(**REQUEST["styles"])
    units = unit_table_profile(**REQUEST["document_units"])
    analysis = unit_table_profile(**REQUEST["analysis_units"])
    views = tuple(row["o"] for row in standard_views(detail_standard=details["f10"]))
    refs = PartRootRefs(details, units, analysis, model_visual_properties(), views)
    inputs = PartRootInput(REQUEST["name"], REQUEST["hatch_name"], 19000)
    allocator = PersistentIds(REQUEST["next_id"], tuple(REQUEST["reserved_ids"]))
    part = MakePartRootMut(inputs, refs, allocator)
    require(type(part) is ArchiveNode, "part factory must return a plain archive node")
    require(part.FieldsValue["f990"].FieldsValue["owner"] is part and part.FieldsValue["f9d0"].FieldsValue["owner"] is part,
            "fresh model dependencies must retain the actual root owner")
    lists = tuple(part.FieldsValue[name] for name in ("f9d8", "fa48", "fa50"))
    require(len({id(node) for node in lists}) == 3 and all(type(node) is ArchiveNode for node in lists),
            "active fresh initializer must allocate three distinct auxiliary lists")
    provenance = REQUEST["provenance"]
    model_header = header(next_id=allocator.NextValue, user_names=(provenance["author"],), company_names=(provenance["company"],),
                          revision_logs=({"object_id": part.FieldsValue["f08"], "name": inputs.NameValue,
                                          "stamps": ({"status": 0, "user_index": 0, "company_index": 0, "timestamp": provenance["created_at"], "comment": provenance["comment"]},)},),
                          created_at=provenance["created_at"], modified_at=provenance["created_at"], updated_at=provenance["created_at"],
                          model_present=True, component_count=0, update_stamp=101, body_stamp=101, license_flags=0, license_type=0)
    wire_header = ReadHeaderGraph(generated_header_bytes(model_header, 19000), 19000)
    created_at = provenance["created_at"]
    config = MakePartConfig(ConfigSpec(inputs.NameValue + " configuration", "", created_at),
                            part, 0, FeatureTarget(2026306, 370108))
    output = SelfFileInput(rf"C:\KitConstruction\{inputs.NameValue}.SLDPRT", created_at)
    wire_header.FieldsValue["f38"] = MakeSelfFile(part, wire_header, config, output)
    header_bytes = WriteHeadGraph(wire_header, 19000)
    config_bytes, configuration = WriteConfigMut(part, 19000, wire_header)
    next_id = allocator.NextValue
    invalid = malformed(inputs, refs, allocator)
    require(allocator.NextValue == next_id, "rejected dependency bindings consumed a persistent identifier")
    require(WriteConfigMut(part, 19000, wire_header)[0] == config_bytes, "rejected construction changed the actual generated graph")
    actual = {"Contents/Config-0": config_bytes, "Contents/Config-0-ModelHeader": header_bytes}
    return {"passed": True, "scope": "complete fresh ordinary part root before configuration and feature attachment",
            "name": inputs.NameValue, "hatch_name": inputs.HatchName, "root_id": part.FieldsValue["f08"], "next_id": next_id,
            "plain_archive_node": True, "self_component_owner": True, "relation_runtime_owner": True,
            "fresh_auxiliary_lists": 3, "view_count": len(views), "malformed": invalid,
            "config_map_counter": configuration.MapValue.CounterValue, "config_usage": configuration.ReportValue,
            "streams": {name: {"bytes": len(data), "sha256": sha256(data).hexdigest(), "data": b64encode(data).decode("ascii")} for name, data in actual.items()},
            "runtime_input_file_reads": len(AUDIT.DeniedReads), "full_part_factory": False,
            "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
