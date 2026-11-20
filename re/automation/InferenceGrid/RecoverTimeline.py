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
            name = name or fields.get("featureBaseName")
            timeline.append({"index": i, "id": node.Identity, "name": name if isinstance(name, str) else None,
                             "native_class": node.ClassName, "suppressed": fields.get("isSuppressed")})
        result.append({"component": component.Identity, "fragment": fragment.Identity, "features": timeline})
    return result


if __name__ == "__main__":
    print(json.dumps(recover(Path(sys.argv[1]))))
