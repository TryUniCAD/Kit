from collections import Counter
from math import atan2, hypot

from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import ReadPrismFrame
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimHandle import ReadDimHandle
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from para.Schema import SCHEMAS
from SweepArchiveLayout import CONTACT, CURVE, PROFILE, SIDE, SWEEP
from SweepModel import require


def only_row(fields, count, items, key):
    row, = fields[items]
    require(fields[count] == 1, f"{items} must own one ordered row")
    return row[key]


def one(layout):
    return only_row(layout, "n", "items", "o")


def no_rows(*layouts):
    return all(layout["n"] == 0 and not layout["items"] for layout in layouts)


def span(link, node):
    return dict(NativeNodeSpan(link, node))


def geometry_point(sketch, position):
    row = sketch["points"][position]
    require(row["kind"] == 0, "sweep sketch point has alternate geometry kind")
    point = row["point"]["pos"]
    return [point["x"], point["y"], point.get("z", 0.0)]


def vector(value):
    return [value.x, value.y, value.z]


def transport(fields, radius, frame):
    body_frame = fields["fc8"]
    nodes = body_frame["nodes"]
    roles = {}
    for node in nodes:
        roles.setdefault(SCHEMAS[node.kind].name, []).append(node)
    require(Counter({kind: len(group) for kind, group in roles.items()}) == {
        "BODY": 1, "SHELL": 1, "FACE": 1, "PLANE": 1, "CIRCLE": 1, "EDGE": 1,
        "LOOP": 1, "HALFEDGE": 2, "REGION": 1,
    }, "section transmit is not the measured single circular planar sheet")
    body, shell, face, plane, circle, edge, loop, region = (
        roles[kind][0] for kind in ("BODY", "SHELL", "FACE", "PLANE", "CIRCLE", "EDGE", "LOOP", "REGION")
    )
    require(body.fields["owner"] == 0 and body.fields["body_type"] == 3
            and body.fields["shell"] == shell.index and shell.fields["body"] == body.index
            and body.fields["edge"] == edge.index and edge.fields["owner"] == body.index
            and body.fields["boundary_curve"] == circle.index and edge.fields["curve"] == circle.index
            and circle.fields["owner"] == edge.index and shell.fields["face"] == face.index
            and face.fields["shell"] == shell.index and face.fields["surface"] == plane.index
            and plane.fields["owner"] == face.index and face.fields["loop"] == loop.index
            and loop.fields["face"] == face.index and body.fields["region"] == region.index
            and region.fields["body"] == body.index and region.fields["shell"] == shell.index,
            "section transmit ownership does not form the measured linked sheet")
    fin, twin = roles["HALFEDGE"]
    require(loop.fields["halfedge"] == edge.fields["halfedge"] == fin.index
            and fin.fields["loop"] == loop.index and fin.fields["edge"] == twin.fields["edge"] == edge.index
            and fin.fields["other"] == twin.index and twin.fields["other"] == fin.index
            and fin.fields["forward"] == fin.fields["backward"] == fin.index
            and twin.fields["loop"] == fin.fields["vertex"] == twin.fields["vertex"] == 0,
            "section circular edge lost its paired halfedge incidence")
    center, normal, axis = tuple(vector(frame.origin)), tuple(vector(frame.z_axis)), tuple(vector(frame.x_axis))
    require(circle.fields["radius"] == radius and circle.fields["centre"] == plane.fields["pvec"] == center
            and circle.fields["normal"] == plane.fields["normal"] == normal
            and circle.fields["x_axis"] == plane.fields["x_axis"] == axis,
            "section kernel circle disagrees with the actual driving sketch")
    return {name: value for name, value in body_frame.items() if name != "nodes"} | {
        "body_type": 3,
        "schema_roles": {kind: [node.index for node in group] for kind, group in roles.items()},
        "radius_m": radius,
        "center_m": center,
        "normal": normal,
    }


def driver(sketch, observation, is_section):
    dims = sketch.FieldsValue["dims"]
    dim = RequireNative(only_row(dims, "ng1", "val_g1", "d"), "sgCircleDim")
    param = RequireNative(dim.FieldsValue["f28"], "moLengthParameter_c")
    view = RequireNative(one(RequireNative(dims["f118"], "suObList").FieldsValue), "moDisplayRadialDim_c")
    display = RequireNative(only_row(view.FieldsValue, "n850", "f850", "o"), "moSkDimHandleRadial_c")
    value = param.FieldsValue["f58"]
    require(value == observation["value_m"] and ReadNativeName(param) == "D1"
            and observation["name"].split("@")[:2] == ["D1", "SweepSection" if is_section else "SweepPath"]
            and observation["display_kind"] == (6 if is_section else 5)
            and observation["driven"] == 2 and observation["read_only"] is False
            and dim.FieldsValue["f80"] == (15 if is_section else 3) and dim.FieldsValue["f90"] == 2
            and display.FieldsValue["ff0"] is sketch and display.FieldsValue["ff8"] == 0
            and ReadDimHandle(dim.FieldsValue["h1"], "sgArcHandle") == 0
            and param.FieldsValue["f20"] == "" and param.FieldsValue["f48"] is None
            and all(param.FieldsValue[name] == 0 for name in ("f0c", "f2c", "f68")),
            "D1 radial display, active value or native arc identity differs")
    return value, dim, param, view, display


def arc_positions(sketch, radius, is_section):
    arc = only_row(sketch, "narcs", "arcs", "arc")
    require(all(sketch[name] == 0 for name in ("nlines", "nellipses", "nsplines"))
            and arc["fd8"] == 1 and arc["fdc_s"] == 0 and arc["fc8_s"] == 1,
            "sweep sketch has alternate entity or orientation choices")
    start, end, center = (geometry_point(sketch, arc[name]) for name in ("fc8_s", "fcc_s", "fdc_s"))
    if is_section:
        require(sketch["npoints"] == 2 and arc["fc8_s"] == arc["fcc_s"]
                and center == [0, 0, 0] and hypot(*start) == radius, "section is not the centered circle")
    else:
        require(sketch["npoints"] == 3 and arc["fcc_s"] == 2
                and start == [0, 0, 0] and center == [0, radius, 0] and end == [radius, radius, 0],
                "path is not the native signed origin-start quadrant")
    return {"center_m": center, "start_m": start, "end_m": end, "sense": arc["fd8"],
            "section_seam_angle_rad": atan2(start[1], start[0]) if is_section else None}


def sketch_relations(sketch, is_section):
    dims = sketch["dims"]
    fixed = only_row(dims, "nlog1", "log_g1", "d")
    require(fixed["f80"] == 17
            and ReadDimHandle(fixed["h1"], "sgPointHandle") == (0 if is_section else 1),
            "fixed sketch point is not the actual center or path start")
    relations = [(17, [0 if is_section else 1])]
    for row in dims["log_g2"]:
        dim = row["d"]
        relations.append((dim["f80"], [ReadDimHandle(dim[name], "sgPointHandle") for name in ("h1", "h2")]))
    require(dims["nlog2"] == len(relations) - 1 and dims["nlog3"] == 0
            and relations == ([(17, [0])] if is_section else [(17, [1]), (26, [0, 1]), (25, [2, 0])]),
            "sweep sketch relation participant order differs")
    return relations


def checked_profiles(link, nodes, curve, profile, observation, is_section):
    component_profile = RequireNative(curve.FieldsValue["f58"], PROFILE)
    ref = component_profile.FieldsValue["ff0"]
    component = RequireNative(component_profile.FieldsValue["f58"], "moUnitComponent_c")
    require(ref["f00"] == NativeNodeId(profile) and nodes[ref["f00"]] is profile
            and component.FieldsValue["owner"] is link.ConfigValue.RootValue
            and component.FieldsValue["has_ext"] == 0 and type(ref["f08"]) is int and ref["f08"] > 0,
            "component profile does not bind the actual same-document earlier feature")
    sketch = RequireNative(profile.FieldsValue["pd_f80"], "sgSketch")
    value, dim, param, view, display = driver(sketch, observation, is_section)
    frame = ReadPrismFrame(profile, link.ConfigValue.RootValue, nodes, FrontOnly=False)
    support_id = profile.FieldsValue["pd_f78"].FieldsValue["ff0"]["f00"]
    support = nodes[support_id]
    require(ReadNativeName(support) == ("Right Plane" if is_section else "Front Plane")
            and vector(frame.origin) == [0, 0, 0] and vector(frame.z_axis) ==
                ([1, 0, 0] if is_section else [0, 0, 1]), "sweep support is not the actual canonical datum")
    fields = curve.FieldsValue
    require(fields["has_fc8"] == int(is_section) and (fields["fb0"], fields["fb8"]) == (0.0, 1.0)
            and all(fields[slot] is None for slot in ("fe0", "fd8", "fe8")),
            "sweep curve uses alternate body or chooser ownership")
    radius = value / 2 if is_section else value
    return {
        "owner": span(link, profile), "feature_id": ref["f00"], "reference_stamp": ref["f08"],
        "component": span(link, component), "component_profile": span(link, component_profile),
        "curve_wrapper": span(link, curve),
        "sketch": span(link, sketch), "support": span(link, support), "support_name": ReadNativeName(support),
        "driver": {"name": "D1", "component": "diameter" if is_section else "radius", "metres": value,
                   "native_id": dim.FieldsValue["f50"], "owners": [span(link, node) for node in (dim, param, view, display)]},
        "arc": arc_positions(sketch.FieldsValue, radius, is_section),
        "relations": sketch_relations(sketch.FieldsValue, is_section),
        "embedded_body": transport(fields, radius, frame) if is_section else None,
    }


def read_owners(link, phases):
    nodes = {NativeNodeId(node): node for node in link.ResolvedValue.RootsValue}
    feature, = (node for node in nodes.values() if node.ClassValue.NameValue == SWEEP)
    section, path = ReadParents(feature)
    require(ReadNativeName(feature) == "OrdinarySweptBoss" and ReadNativeName(section) == "SweepSection"
            and ReadNativeName(path) == "SweepPath", "sweep ordered parents disagree with native author")
    fields = feature.FieldsValue
    data = fields["f820"]
    section_curve = RequireNative(one(data["f2c0"]), CURVE)
    contact = RequireNative(one(data["f2e0"]), CONTACT)
    path_curve = RequireNative(contact.FieldsValue["fe8"], CURVE)
    require(section_curve is not path_curve and section.EndOffset <= path.StartOffset
            and path.EndOffset <= feature.StartOffset and data["f298"] is data["f2a0"] is None
            and no_rows(*(data[name] for name in ("f300", "f98", "fe0", "f320", "f340")))
            and no_rows(contact.FieldsValue["f50"]) and contact.FieldsValue["fa0"] is contact.FieldsValue["fe0"] is None,
            "sweep supports use alternate reference, guide or contact data")
    side = [entry.EntryValue for entry in link.ResolvedValue.MapValue.EntriesValue
            if getattr(getattr(entry.EntryValue, "ClassValue", None), "NameValue", None) == SIDE]
    require(side and all(rep.FieldsValue["f10"]["f10"].FieldsValue["f10"]["f00"] == NativeNodeId(feature)
                         for rep in side), "side surface identifiers do not point to the live sweep creator")
    section_data = checked_profiles(link, nodes, section_curve, section, phases["section"], True)
    path_data = checked_profiles(link, nodes, path_curve, path, phases["path"], False)
    require(section_data["driver"]["native_id"] != path_data["driver"]["native_id"],
            "section and path D1 use the same live dimension identity")
    return {
        "feature": span(link, feature), "feature_id": NativeNodeId(feature),
        "section": section_data, "path": path_data, "path_contact": span(link, contact),
        "side_surface_identifiers": [{"owner": span(link, rep), "f38": rep.FieldsValue["f38"],
                                      "f3c": rep.FieldsValue["f3c"]} for rep in side],
        "outer_scalar": {name: fields[name] for name in ("fc0c", "fc10", "fc14", "fc18", "fc1c", "f80c", "fc20", "fc24")},
        "inline_scalar": {name: value for name, value in data.items() if type(value) in (int, float)},
        "contact_scalar": {name: value for name, value in contact.FieldsValue.items() if type(value) in (int, float)},
    }
