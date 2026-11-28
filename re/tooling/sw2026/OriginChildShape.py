from __future__ import annotations

from OriginPairChecks import require
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


def slot(handle, expected):
    require(handle.ClassValue == RuntimeClass(expected, 1), "anchor handle has a foreign concrete class")
    value = handle.FieldsValue["idx"]
    return value if value < 0x777f else handle.FieldsValue["f18"]


def endpoint(line, name):
    value = line[name + "_s"]
    return value if value < 0xffff else line[name]


def inspect_child(roots, kind):
    profile, = [value for value in roots if value.ClassValue == RuntimeClass("moProfileFeature_c", 1)]
    origin, = [value for value in roots if value.ClassValue == RuntimeClass("moOriginProfileFeature_c", 1)]
    sketch = ArchiveNode.RequireNode(profile.FieldsValue["pd_f80"])
    fields, origin_sketch = sketch.FieldsValue, ArchiveNode.RequireNode(origin.FieldsValue["pd_f80"])
    points, lines, dims = fields["points"], fields["lines"], fields["dims"]
    relations = dims["log_g2"]
    center = kind == "center-anchored"
    require(kind in ("corner-anchored", "center-anchored") and len(points) == fields["npoints"] == 5 + int(center)
            and len(lines) == fields["nlines"] == 4 + 2 * int(center)
            and len(relations) == dims["nlog2"] == 1 + 2 * int(center), "anchor geometry or relation counts differ")
    require(fields["f130"] == 5 and fields["f56c"] == len(lines) + 1
            and fields["f140"]["f08"] == len(points) + 1 and fields["f140"]["f0c"] == len(lines) + 1,
            "anchor contour and creation frontiers differ")
    external = points[-1]["point"]
    require(points[-1]["kind"] == 1 and external["fe4"] == 6 and external["pos"] == {"x": 0.0, "y": 0.0}, "anchor lost its actual external origin point")
    selected = ArchiveNode.RequireNode(ArchiveNode.RequireNode(ArchiveNode.RequireNode(external["ext"]).FieldsValue["f08"]).FieldsValue["f58"])
    require(selected.ClassValue == RuntimeClass("moCompSketchEntHandle_c", 1)
            and selected.FieldsValue["ff0"]["f00"] == origin.FieldsValue["f08"]
            and selected.FieldsValue["f100"] == origin_sketch.FieldsValue["points"][0]["point"]["f08"]
            and slot(ArchiveNode.RequireNode(selected.FieldsValue["f0f8"]), "sgPointHandle") == 0,
            "anchor external reference lost the actual origin point or persistent mark")
    local_slot = 4 if center else 0
    last = relations[-1]["d"]
    require(last["f80"] == 9 and slot(ArchiveNode.RequireNode(last["h1"]), "sgPointHandle") == len(points) - 1
            and slot(ArchiveNode.RequireNode(last["h2"]), "sgPointHandle") == local_slot,
            "anchor origin coincidence lost its actual endpoint roles")
    for index, row in enumerate(lines[:4]):
        line = row["line"]
        require(row["flags"] == 0 and endpoint(line, "fc8") == index and endpoint(line, "fcc") == (index + 1) % 4,
                "anchor changed the actual four edge body contour")
    if center:
        local = points[local_slot]["point"]
        require(local["fe4"] == 1 and local["fe8"] == 0 and local["f20"] == 3
                and local["pos"] == external["pos"], "center point lost its three actual coincidence references")
        for index, row in enumerate(relations[:-1]):
            relation = row["d"]
            line_slot = slot(ArchiveNode.RequireNode(relation["h2"]), "sgLineHandle")
            require(relation["f80"] == 9 and slot(ArchiveNode.RequireNode(relation["h1"]), "sgPointHandle") == local_slot
                    and line_slot == 4 + index, "center point on diagonal relation lost its actual line")
            line = lines[line_slot]["line"]
            require(lines[line_slot]["flags"] == 2 and line["f54"] & 8 and line["f20"] == 1
                    and line["fd0"] == 0 and line["f08"] == 0 and line["f0c"] == line_slot + 1
                    and endpoint(line, "fc8") == index and endpoint(line, "fcc") == index + 2,
                    "center diagonal constructor or endpoint ownership differs")
        require(all(row["point"]["fe8"] == 3 for row in points[:4]), "center diagonal endpoint incidences differ")
    return {"anchor_kind": kind, "wire_points": len(points), "visible_lines": len(lines), "construction_diagonals": 2 if center else 0,
            "origin_coincidences": len(relations), "actual_origin_id": origin.FieldsValue["f08"],
            "contour_frontier": fields["f130"], "next_line_id": fields["f56c"],
            "native_acceptance": False}
