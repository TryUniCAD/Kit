from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile

from convert.Geometry import Opencascade as occ
from FcstdRectangleOwners01 import (
    close_point,
    point,
    rectangular_source_measure,
    require,
    source_objects,
    topology_compare,
)
from interchange.brep.Curves.BrepCurves import LineCurve


def fingerprint(raw):
    return sha256(raw).hexdigest()


def wire_topology(payload):
    tokens = occ.Tokens(payload)
    occ.ExpectHeader(tokens)
    locations = occ.ModelLocations(tokens)
    curves_2d, curves = occ.ReadModelCurves(tokens, "source_wire")
    occ.ZeroTable(tokens, b"Polygon3D")
    occ.ZeroTable(tokens, b"PolygonOnTriangulations")
    surfaces = occ.ReadModelSurfs(tokens, "source_wire")
    occ.ZeroTable(tokens, b"Triangulations")
    count = occ.ReadCount(tokens, b"TShapes", occ.KMaxShapes)
    require(
        not curves_2d and not surfaces and len(curves) == 4 and count == 9,
        "source sketch cache has unqualified topology or geometry",
    )
    records = occ.ShapeRecords(
        tokens, count, len(curves), curves_2d, len(surfaces), len(locations)
    )
    root = occ.ReadReference(tokens, count, len(locations))
    require(
        root is not None and root.Orientation == "+" and tokens.PeekToken() is None,
        "source sketch cache has incomplete wire framing",
    )
    curves, _, records, root = occ.ApplyLocations(
        curves, surfaces, records, root, locations, "source_wire"
    )
    wire = records[root.RecordA]
    require(
        wire.KindValue == b"Wi" and len(wire.Children) == 4 and len(records) == 9,
        "source sketch cache does not own a single four-edge wire",
    )
    return wire.Children, records, curves


def edge_points(link, records, curves):
    edge = records[link.RecordA]
    require(
        link.Orientation == "+"
        and link.KLocation == 0
        and edge.KindValue == b"Ed"
        and type(edge.GeometryA) is occ.EdgeData
        and len(edge.Children) == 2,
        "source sketch cache has another edge traversal",
    )
    geometry = edge.GeometryA
    curve = curves[geometry.Curve - 1]
    require(
        type(curve) is LineCurve
        and geometry.KLocation == 0
        and geometry.LastValue > geometry.FirstValue
        and tuple(child.Orientation for child in edge.Children) == ("+", "-"),
        "source sketch cache lacks its bounded line trim",
    )
    result = []
    for child, value in zip(
        edge.Children, (geometry.FirstValue, geometry.LastValue), strict=True
    ):
        vertex = records[child.RecordA]
        require(
            child.KLocation == 0
            and vertex.KindValue == b"Ve"
            and type(vertex.GeometryA) is occ.VertexData,
            "source sketch cache has another vertex owner",
        )
        position = point(vertex.GeometryA.Point)
        calculated = tuple(
            a + value * b
            for a, b in zip(point(curve.origin), point(curve.direction), strict=True)
        )
        require(
            close_point(position, calculated),
            "source sketch cache trim misses its actual vertex",
        )
        result.append(position)
    return (
        tuple(result),
        tuple(child.RecordA for child in edge.Children),
        geometry.Curve,
    )


def inspect_sketch(payload, sketch):
    links, records, curves = wire_topology(payload)
    rows = [edge_points(link, records, curves) for link in links]
    require(
        len({row[2] for row in rows}) == 4
        and len({row[1][0] for row in rows}) == 4
        and all(
            a[1][1] == b[1][0] for a, b in zip(rows, (*rows[1:], rows[0]), strict=True)
        ),
        "source sketch cache lacks the actual shared endpoint identities",
    )
    source_lines = tuple(
        (
            (line.geometry.start.x, line.geometry.start.y, 0.0),
            (line.geometry.end.x, line.geometry.end.y, 0.0),
        )
        for line in sketch.entities
    )
    require(
        any(
            all(
                close_point(actual, expected)
                for row, ordered in zip(
                    rows[offset:] + rows[:offset], source_lines, strict=True
                )
                for actual, expected in zip(row[0], ordered, strict=True)
            )
            for offset in range(len(rows))
        ),
        "source sketch cache differs from the actual editable line ring",
    )
    return {"vertices": 4, "edges": 4, "ordered_editable_line_ring": True}


def owned_shape(payload, item, property_name, source_sha):
    properties = item["properties"]
    declared = properties[property_name]
    (part,) = declared["children"]
    path = part["attributes"]["file"]
    require(
        declared["tag"] == "Property"
        and declared["attributes"]["name"] == property_name
        and declared["attributes"]["type"] == "Part::PropertyPartShape"
        and part["tag"] == "Part"
        and part["attributes"] == {"file": path}
        and payload.kind == "shape"
        and payload.format_id == "opencascade"
        and payload.source_stream == path
        and payload.attributes["freecad_object"] == item["name"]
        and payload.attributes["freecad_property"] == property_name
        and payload.attributes["freecad_property_data"] == declared
        and payload.attributes["freecad.native_document_sha256"] == source_sha
        and payload.data is not None
        and fingerprint(payload.data) == payload.sha256,
        "saved shape does not belong to its actual source property",
    )
    return path


def compare_solids(source, target, body_id):
    require(len(target.bodies) == 1, "generated lineage has more than one design body")
    target = replace(
        target, bodies=(replace(target.bodies[0], design_body_id=body_id),)
    )
    measured = topology_compare(source, target, body_id)
    return {
        key: measured[key]
        for key in ("vertices", "edges", "faces", "coordinate_tolerance_mm")
    }


def geometry_owners(document, generated):
    (sketch,) = document.sketches
    (feature,) = document.feature_timeline
    (body,) = document.bodies
    owners = source_objects(document)
    source_sha = document.source.sha256
    require(
        document.brep is not None
        and generated.brep is not None
        and body.final_feature_id == feature.id
        and not feature.input_feature_ids,
        "lineage comparison requires the actual first source and target solids",
    )
    entries = (
        (body.attributes["freecad"]["name"], "Shape"),
        (sketch.attributes["freecad"]["name"], "Shape"),
        (feature.attributes["freecad"]["name"], "AddSubShape"),
        (feature.attributes["freecad"]["name"], "Shape"),
    )
    inventory = {payload.id: payload for payload in document.brep_payloads}
    replay = inventory["freecad:native-document"]
    binding = inventory["freecad:native-document-binding"]
    require(
        replay.sha256 == source_sha
        and fingerprint(replay.data) == source_sha
        and binding.data == bytes.fromhex(source_sha)
        and fingerprint(binding.data) == binding.sha256,
        "source replay binding differs from its exact archive",
    )
    shapes = {}
    paths = []
    with ZipFile(BytesIO(replay.data)) as opened:
        original_entries = {
            entry: opened.read(entry)
            for entry in document.metadata["freecad"]["entry_order"]
        }
    for index, (name, prop) in enumerate(entries):
        key = f"freecad:brep:{name}:{prop}"
        (payload,) = (entry for entry in document.brep_payloads if entry.id == key)
        path = owned_shape(payload, owners[name], prop, source_sha)
        require(
            payload.data == original_entries[path],
            "saved shape differs from its exact original member",
        )
        paths.append(path)
        if index == 1:
            matched = inspect_sketch(payload.data, sketch)
        else:
            model = occ.DecodeAsciiBrep(
                payload.data, IdPrefix=f"source_shape_{index}", DesignBodyId=body.id
            )
            require(
                model is not None, "source solid owner has unreadable OCCT boundary"
            )
            matched = compare_solids(model, generated.brep, body.id)
        shapes[key] = {
            "sha256": payload.sha256,
            "bytes": len(payload.data),
            "boundary": matched,
        }
    inventory = {payload.id: payload for payload in document.brep_payloads}
    require(
        len(inventory) == len(document.brep_payloads) == 6
        and set(inventory)
        == {*shapes, "freecad:native-document", "freecad:native-document-binding"}
        and tuple(paths) == tuple(document.metadata["freecad"]["entry_order"])
        and body.attributes["brep_payload_ids"] == [next(iter(shapes))]
        and inventory[next(iter(shapes))].attributes.get("body_id") == body.id
        and inventory[next(reversed(shapes))].attributes.get("feature_id")
        == feature.id,
        "source shape roles are missing or not attached to the recorded Body and Pad",
    )
    return {
        "owned_boundaries": shapes,
        "metrics": rectangular_source_measure(document.brep),
        "source_only": {
            name: inventory[name].sha256
            for name in ("freecad:native-document", "freecad:native-document-binding")
        },
        "occt_id_transfer": False,
    }
