# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
from pathlib import Path
import sys

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, ResolveField
from convert.adapters.Fusion.Native.Graph.OrderedFeatures import OrderedFeatures
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Extrude.ExtrudeShape import KBooleanCodes
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument


def parameters(graph, component, feature_ids):
    table = ResolveField(graph, component, "rParameterTable", "ParameterTable")
    if graph.Resolve(table.Fields["rParent"], table.SegmentId) != component:
        raise ValueError("parameter table has a different component parent")
    result = []
    for node in LinkedNodes(graph, table, "children"):
        fields = node.Fields
        row = {"id": node.Identity}
        try:
            if node.ClassName != "Parameter" or graph.Resolve(fields["rParent"], node.SegmentId) != table:
                raise ValueError("invalid parameter table member")
            binding = ResolveField(graph, node, "dcParameter", "DcDoubleParameter")
            if ResolveField(graph, binding, "parameter", "Parameter") != node:
                raise ValueError("parameter binding is not reciprocal")
            owner = graph.Resolve(binding.Fields["rrOwnerFeature"], binding.SegmentId)
            if owner.Identity not in feature_ids or graph.Resolve(binding.Fields["rParentFeature"], binding.SegmentId) != owner:
                raise ValueError("parameter owner differs from saved feature order")
            if type(fields["value"]) not in (int, float) or fields["value"] != binding.Fields["value"]:
                raise ValueError("numeric parameter values disagree")
            row.update(name=fields["userName"], role=fields["name"], unit=fields["unit"],
                       expression=fields["expression"], value=fields["value"], owner=owner.Identity, binding=binding.Identity)
        except (KeyError, ValueError) as error:
            row["refusal"] = str(error)[:256]
        result.append(row)
    return result


def recover(path, registry=None):
    bindings = json.loads((registry or Path(__file__).with_name("TimelineNames.json")).read_bytes())
    graph = BuildGraph(ReadDocument(path.read_bytes()))
    result = []
    for component in graph.ByClass("FusionComponent"):
        fragment, features = OrderedFeatures(graph, component)
        timeline = []
        for i, node in enumerate(features):
            fields = node.Fields
            name = fields.get("featureUserName")
            possible = []
            if not name and node.ClassName in bindings:
                link, target_class = bindings[node.ClassName]
                name = ResolveField(graph, node, link, target_class).Fields.get("userName")
            if not name:
                for key, reference in fields.items():
                    if not key.startswith("r"):
                        continue
                    try:
                        target = graph.Resolve(reference, node.SegmentId)
                    except ValueError:
                        continue
                    label = target.Fields.get("userName")
                    if isinstance(label, str) and label:
                        possible.append({"field": key, "class": target.ClassName, "name": label})
            name = name or fields.get("featureBaseName")
            timeline.append({"index": i, "id": node.Identity, "name": name if isinstance(name, str) else None,
                             "native_class": node.ClassName, "suppressed": fields.get("isSuppressed")})
            if any(field.FieldName.endswith(("Type", "Mode")) for field in node.Groups[0].Fields):
                shape = {}
                for field in node.Groups[0].Fields:
                    key, value = field.FieldName, field.Value
                    if type(value) in (int, bool) or value is None:
                        shape[key] = value
                    elif key.startswith("r") and hasattr(value, "ObjectId"):
                        target = graph.Resolve(value, node.SegmentId)
                        shape[key] = target.ClassName
                timeline[-1]["parameter_context"] = {"class_guid": node.Groups[0].ClassGuid, "fields": shape}
            if possible:
                timeline[-1]["name_candidates"] = possible
            if node.ClassName == "DcExtrudeFeature":
                code = fields.get("booleanOperation")
                timeline[-1]["operation"] = next((operation for operation, value in KBooleanCodes.items() if type(code) is int and code == value), None)
                thin = fields.get("thinExtrude")
                timeline[-1]["thin"] = thin if type(thin) is bool else None
        entry = {"component": component.Identity, "fragment": fragment.Identity, "features": timeline}
        try:
            entry["parameters"] = parameters(graph, component, {node.Identity for node in features})
        except (KeyError, ValueError) as error:
            entry["parameter_refusal"] = str(error)[:256]
        result.append(entry)
    return result


if __name__ == "__main__":
    try:
        print(json.dumps(recover(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) == 3 else None)))
    except (KeyError, ValueError) as error:
        print(json.dumps({"refusal": str(error)[:1024]}))
        sys.exit(2)
