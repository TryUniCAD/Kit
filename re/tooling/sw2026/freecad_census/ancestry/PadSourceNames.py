from dataclasses import asdict
from hashlib import sha256
from re import findall

from C130GeometryOwners import edge_points, inspect_sketch, wire_topology
from FcstdRectangleOwners01 import require, source_objects
from PadElementMap import parse_map
from PadNameTable import count_text, read_geometry_seed, read_string_table, resolve_seed
from PadOccurrences import KINDS

BODY = "freecad:brep:Body:Shape"
SKETCH = "freecad:brep:Sketch:Shape"
PAD_SHAPE = "freecad:brep:Pad:Shape"
PAD_TOOL = "freecad:brep:Pad:AddSubShape"
SHAPE_ROLES = (BODY, SKETCH, PAD_TOOL, PAD_SHAPE)
TABLE = "StringHasher.Table.txt"


def sha(data):
    return sha256(data).hexdigest()


def physical_shape_members(document, members, modern):
    owners = source_objects(document)
    actual = {row.id: row for row in document.brep_payloads}
    require(len(actual) == len(document.brep_payloads), "repeated source shape role")
    result = {}
    map_names = set()
    for identity in SHAPE_ROLES:
        payload = actual[identity]
        object_name = payload.attributes["freecad_object"]
        prop_name = payload.attributes["freecad_property"]
        property_row = owners[object_name]["properties"][prop_name]
        part, *links = property_row["children"]
        label = payload.source_stream
        require(
            property_row["attributes"]["type"] == "Part::PropertyPartShape"
            and part["tag"] == "Part"
            and part["attributes"]["file"] == label
            and payload.attributes["freecad_property_data"] == property_row
            and payload.attributes["freecad_part_attributes"] == part["attributes"]
            and payload.attributes["freecad.native_document_sha256"]
            == document.source.sha256
            and payload.data == members[label]
            and payload.sha256 == sha(payload.data),
            "stored shape differs from its actual original property owner",
        )
        children = payload.attributes.get("freecad_sidecars", [])
        if modern:
            require(
                tuple(row["tag"] for row in links) == ("ElementMap", "ElementMap2")
                and links[0]["attributes"] == {"count": "1", "new": "1"}
                and links[0].get("children")
                == [
                    {"tag": "Element", "attributes": {"key": "Dummy", "value": "Dummy"}}
                ]
                and set(links[1]["attributes"]) == {"file"}
                and "ElementMap" in part["attributes"],
                "modern shape has a different map property owner",
            )
            map_name = links[1]["attributes"]["file"]
            require(
                map_name not in map_names
                and children
                == [{"source_stream": map_name, "data": members[map_name]}],
                "map member differs from its actual retained shape owner",
            )
            map_names.add(map_name)
            result[identity] = (payload, members[map_name])
        else:
            require(
                not links and not children,
                "legacy shape carries an alternate element map",
            )
            result[identity] = (payload, None)
    maps = {name for name in members if name.endswith(".Map.txt")}
    require(
        maps == map_names
        and len(maps) == (4 if modern else 0)
        and bool(TABLE in members) == modern
        and ("string_hasher" in document.metadata["freecad"]) == modern,
        "original member inventory disagrees with its element-map mode",
    )
    if modern:
        table = document.metadata["freecad"]["string_hasher"]
        require(
            table["entries"] == [{"source_stream": TABLE, "data": members[TABLE]}]
            and table["nodes"][-1]["attributes"] == {"file": TABLE},
            "element string table differs from its actual document owner",
        )
    return result


def decode_name(row, table):
    if row.string_id:
        seed = resolve_seed(table, row.string_id, row.index)
    else:
        seed = read_geometry_seed(row.literal)
    return seed, (*seed.suffixes, row.postfix)


def actual_geometry(sketch):
    result = {}
    for entity in sketch.entities:
        row = entity.attributes["freecad"]
        (extensions,) = (
            child for child in row["children"] if child["tag"] == "GeoExtensions"
        )
        (owner,) = extensions["children"]
        number = count_text(row["attributes"]["id"])
        require(
            number not in result
            and str(number) == entity.attributes["freecad_geometry_id"]
            and owner["tag"] == "GeoExtension"
            and owner["attributes"]["type"] == "Sketcher::SketchGeometryExtension"
            and owner["attributes"]["id"] == str(number),
            "element alias refers to an unowned sketch geometry id",
        )
        result[number] = entity
    require(
        len(result) == 4,
        "source local naming requires four separate sketch geometry owners",
    )
    return result


def endpoint_codes(entity):
    return (
        ("0" if entity.geometry.start.x == 0 else "1")
        + ("0" if entity.geometry.start.y == 0 else "1"),
        ("0" if entity.geometry.end.x == 0 else "1")
        + ("0" if entity.geometry.end.y == 0 else "1"),
    )


def range_code(left, right):
    return "".join(a if a == b else "*" for a, b in zip(left, right, strict=True))


def point_code(point):
    x, y, _ = point
    return ("0" if x == 0 else "1") + ("0" if y == 0 else "1")


def sketch_roles(payload, sketch):
    inspect_sketch(payload.data, sketch)
    links, records, curves = wire_topology(payload.data)
    edges, vertices = [], {}
    for ref in links:
        coords, ids, _ = edge_points(ref, records, curves)
        a, b = tuple(point_code(point) for point in coords)
        edges.append(range_code(a, b))
        for idx, coord in zip(ids, (a, b), strict=True):
            require(
                idx not in vertices or vertices[idx] == coord,
                "ambiguous source sketch point identity",
            )
            vertices[idx] = coord
    return {"Edge": edges, "Vertex": list(vertices.values())}


def read_group_rows(maps, allowed_kinds, counts):
    require(
        tuple(group.kind for group in maps.groups) == tuple(allowed_kinds),
        "element map has wrong native shape classes",
    )
    result = {}
    for group in maps.groups:
        require(
            not group.children
            and len(group.names) == counts[group.kind] + 1
            and group.names[0] == ()
            and all(group.names[1:]),
            "element name array lacks the empty ordinal zero or complete boundary rows",
        )
        result[group.kind] = group.names[1:]
    return result


def check_alias(kind, role, seed, entity, suffixes, sketch_id, source_solid):
    a, b = endpoint_codes(entity)
    expected = None if seed.endpoint is None else (a, b)[seed.endpoint - 1]
    require(suffixes[0] == ";SKT", "mapped role lacks its original sketch element tag")
    if not source_solid:
        require(
            suffixes == (";SKT",)
            and (
                role == expected
                if kind == "Vertex"
                else seed.endpoint is None and role == range_code(a, b)
            ),
            "sketch named ordinal points to a foreign physical geometry",
        )
        return
    owners = [
        row
        for suffix in suffixes
        for row in findall(r";:H([0-9a-f]+)(?::[0-9a-f]+)?,([EFV])", suffix)
    ]
    require(
        owners
        and owners[-1][1] == kind[0]
        and all(int(tag, 16) == sketch_id for tag, _ in owners),
        "pad element name does not own its actual sketch source tag",
    )
    lateral = range_code(a, b)
    if kind == "Face":
        matches = seed.endpoint is None and (
            role in ("**0", "**1") or role == lateral + "*"
        )
    elif kind == "Edge":
        matches = (
            role == expected + "*"
            if expected is not None
            else role[:2] == lateral and role[2] in "01"
        )
    else:
        matches = (
            role[:2] in ((expected,) if expected is not None else (a, b))
            and role[2] in "01"
        )
    require(matches, "pad named ordinal points to a foreign physical geometry")


def resolve_map_rows(rows, roles, geometry, table, sketch_id, source_solid):
    records = {}
    names_seen = set()
    for kind, items in rows.items():
        result = []
        for ordinal, (aliases, role) in enumerate(
            zip(items, roles[kind], strict=True), 1
        ):
            mapped = []
            for alias in aliases:
                key = (alias.literal, alias.string_id, alias.index, alias.postfix)
                require(
                    key not in names_seen,
                    "one mapped name repeats on different native ordinals",
                )
                names_seen.add(key)
                seed, suffixes = decode_name(alias, table)
                entity = geometry[seed.geometry]
                check_alias(kind, role, seed, entity, suffixes, sketch_id, source_solid)
                mapped.append(
                    {
                        "actual_sketch_entity": entity.id,
                        "geometry_id": seed.geometry,
                        "endpoint": seed.endpoint,
                        "stored_subindex": alias.index,
                        "string_ids": seed.string_ids,
                        "retained_related_ids": alias.related_ids,
                        "suffixes": suffixes,
                    }
                )
            result.append(
                {"ordinal": ordinal, "physical_role": role, "aliases": mapped}
            )
        records[kind] = result
    return records


def read_body_ranges(root, pad_map, pad_id, actual_roles):
    require(
        tuple(row.kind for row in root.groups) == KINDS,
        "body map has wrong typed boundary groups",
    )
    result = {}
    for group in root.groups:
        expected = f";:H{pad_id:x},{group.kind[0]}"
        ranges = group.children
        require(
            len(ranges) == 1 and not group.names,
            "body map lacks one pure Pad child range",
        )
        (child,) = ranges
        require(
            (
                child.first,
                child.offset,
                child.count,
                child.tag,
                child.map_index,
                child.postfix,
            )
            == (1, 0, len(actual_roles[group.kind]), pad_id, 1, expected)
            and dict((value.kind, value) for value in pad_map.groups)[group.kind].names,
            "body map range does not name the actual Pad result owner",
        )
        result[group.kind] = asdict(child)
    return result


def verify_modern(document, split, members, roles):
    source_objects_map = source_objects(document)
    pad_id = count_text(source_objects_map["Pad"]["object_id"])
    sketch_id = count_text(source_objects_map["Sketch"]["object_id"])
    table = read_string_table(members[TABLE])
    maps = {role: parse_map(data, table) for role, (_, data) in split.items()}
    require(
        tuple(len(maps[key]) for key in SHAPE_ROLES) == (2, 1, 1, 1),
        "source map ownership has more than the actual body and child maps",
    )
    (pad_map,) = maps[PAD_SHAPE]
    (tool_map,) = maps[PAD_TOOL]
    (wire_map,) = maps[SKETCH]
    body_child, body_root = maps[BODY]
    require(
        body_child == pad_map
        and pad_map.groups == tool_map.groups
        and len(
            {value.identity for value in (body_root, body_child, tool_map, wire_map)}
        )
        == 4,
        "body map does not embed the exact Pad result map",
    )
    counts = {kind: len(values) for kind, values in roles[BODY].items()}
    shapes = {
        row: {kind: [value.role for value in roles[row][kind]] for kind in KINDS}
        for row in (BODY, PAD_SHAPE, PAD_TOOL)
    }
    require(
        shapes[BODY] == shapes[PAD_SHAPE] == shapes[PAD_TOOL],
        "body ordinal does not resolve the same actual Pad child boundary",
    )
    child_ranges = read_body_ranges(body_root, pad_map, pad_id, shapes[BODY])
    (sketch,) = document.sketches
    geometry = actual_geometry(sketch)
    sketch_values = sketch_roles(split[SKETCH][0], sketch)
    sketch_rows = read_group_rows(
        wire_map,
        ("Edge", "Vertex"),
        {kind: len(values) for kind, values in sketch_values.items()},
    )
    pad_rows = read_group_rows(pad_map, KINDS, counts)
    pad_aliases = resolve_map_rows(
        pad_rows, shapes[PAD_SHAPE], geometry, table, sketch_id, True
    )
    return {
        "string_table_rows": len(table),
        "string_table_sha256": sha(members[TABLE]),
        "map_sha256": {role: sha(value[1]) for role, value in split.items()},
        "pad_owner_id": pad_id,
        "sketch_owner_id": sketch_id,
        "body_child_map_id": body_child.identity,
        "body_child_ranges": child_ranges,
        "actual_sketch_ordinal_aliases": resolve_map_rows(
            sketch_rows, sketch_values, geometry, table, sketch_id, False
        ),
        "actual_pad_ordinal_aliases": pad_aliases,
        "counts": {
            kind: {
                "rows": len(cells),
                "aliases": sum(len(cell["aliases"]) for cell in cells),
            }
            for kind, cells in pad_aliases.items()
        },
    }
