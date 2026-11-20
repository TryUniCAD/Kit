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
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.OrderedFeatures import OrderedFeatures
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Extrude.ExtrudeShape import KBooleanCodes
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument


def recover(path):
    graph = BuildGraph(ReadDocument(path.read_bytes()))
    result = []
    for component in graph.ByClass("FusionComponent"):
        fragment, features = OrderedFeatures(graph, component)
        timeline = []
        for i, node in enumerate(features):
            fields = node.Fields
            name = fields.get("featureUserName")
            if not name and node.ClassName == "DcSketch":
                name = ResolveField(graph, node, "rSketch", "MSketch").Fields.get("userName")
            if not name and node.ClassName == "DcWorkPlane":
                name = ResolveField(graph, node, "rWorkPlane", "WorkPlane").Fields.get("userName")
            name = name or fields.get("featureBaseName")
            timeline.append({"index": i, "id": node.Identity, "name": name if isinstance(name, str) else None,
                             "native_class": node.ClassName, "suppressed": fields.get("isSuppressed")})
            if node.ClassName == "DcExtrudeFeature":
                code = fields.get("booleanOperation")
                timeline[-1]["operation"] = next((operation for operation, value in KBooleanCodes.items() if type(code) is int and code == value), None)
                thin = fields.get("thinExtrude")
                timeline[-1]["thin"] = thin if type(thin) is bool else None
        result.append({"component": component.Identity, "fragment": fragment.Identity, "features": timeline})
    return result


if __name__ == "__main__":
    try:
        print(json.dumps(recover(Path(sys.argv[1]))))
    except ValueError as error:
        print(json.dumps({"refusal": str(error)[:1024]}))
        sys.exit(2)
