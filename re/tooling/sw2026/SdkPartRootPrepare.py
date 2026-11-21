from __future__ import annotations

from base64 import b64decode
from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

CODECS = tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def require(value, message):
    if not value:
        raise ValueError(message)


def require_node(node, class_name):
    require(type(node) is ArchiveNode and node.ClassValue == RuntimeClass(class_name, 1), "prepared model graph has the wrong concrete owner")
    return node


def main():
    built = REQUEST["build"]
    buffers = {name: b64decode(row["data"], validate=True) for name, row in built["streams"].items()}
    for name, data in buffers.items():
        require(len(data) == built["streams"][name]["bytes"] and sha256(data).hexdigest() == built["streams"][name]["sha256"], "generated stream custody differs")
    model_header = ReadHeaderGraph(buffers["Contents/Config-0-ModelHeader"], 19000)
    configuration = ReadConfigMut(buffers["Contents/Config-0"], 19000, model_header)
    part = require_node(configuration.RootValue, "moPart_c")
    fields = part.FieldsValue
    require(fields["f08"] == built["root_id"] and model_header.FieldsValue["f08"] == built["next_id"], "prepared model or header persistent identity differs")
    require(fields["f18"].FieldsValue["f08"] == REQUEST["request"]["name"], "prepared model name differs from authored input")
    require(fields["f1418"].FieldsValue["f08"] == REQUEST["request"]["hatch_name"], "prepared hatch name differs from authored input")
    component = require_node(fields["f990"], "moUnitComponent_c")
    require(component.FieldsValue["owner"] is part and component.FieldsValue["has_ext"] == 0, "prepared self component lost the actual model cycle")
    relations = require_node(fields["f9d0"], "moRelMgr_c")
    require("owner" not in relations.FieldsValue, "raw relation manager must not fabricate its runtime owner")
    require(relations.FieldsValue["ff4"] == relations.FieldsValue["f1b0"] == -1 and relations.FieldsValue["n1c0"] == 0,
            "prepared relation manager constructor state differs")
    lists = tuple(require_node(fields[name], "suObList") for name in ("f9d8", "fa48", "fa50"))
    require(len({id(node) for node in lists}) == 3 and all(node.FieldsValue["n"] == 0 and not node.FieldsValue["items"] for node in lists),
            "prepared active fresh lists are absent merged or nonempty")
    require_node(fields["f9b8"], "moUnitsTable_c")
    require_node(fields["f9c0"], "moUnitsTable_c")
    require(fields["f9b8"] is not fields["f9c0"], "prepared document and analysis units lost independent ownership")
    views = tuple(require_node(row["o"], "moView_c") for row in fields["f9f8"])
    require(len(views) == len({id(node) for node in views}) == 10 and all(node.FieldsValue["f360"] == index for index, node in enumerate(views)),
            "prepared ordinary view ownership or indexed order differs")
    require(fields["f2f8"] is None and not fields["f60"]["list"]["items"], "root component must not invent a configuration manager or features")
    encoded, repeated = WriteConfigMut(part, 19000, model_header)
    actual = {"Contents/Config-0": encoded, "Contents/Config-0-ModelHeader": WriteHeadGraph(model_header, 19000)}
    comparisons = {name: {"bytes": len(data), "sha256": sha256(data).hexdigest(), "byte_identity": data == buffers[name]} for name, data in actual.items()}
    require(all(row["byte_identity"] for row in comparisons.values()), "prepared root graph failed complete SDK stream identity")
    require(configuration.ReportValue["completed"] and not configuration.ReportValue["missing_schemas"] and not configuration.ReportValue["provisional_schemas"], "prepared root uses incomplete grammar")
    require(repeated.MapValue.CounterValue == configuration.MapValue.CounterValue == built["config_map_counter"], "prepared root changed its actual archive map")
    return {"passed": True, "scope": "separate SDK preparation of fresh part root component",
            "self_component_cycle": True, "relation_runtime_owner_absent": True, "active_fresh_lists": 3,
            "independent_units": True, "ordered_views": 10, "config_map_counter": configuration.MapValue.CounterValue,
            "config_usage": configuration.ReportValue, "streams": comparisons, "runtime_input_file_reads": len(AUDIT.DeniedReads),
            "full_part_factory": False, "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
