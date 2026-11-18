from __future__ import annotations

from math import isclose

from OriginPortableGraph import check_drive, endpoint, require, scalar


def one(values, label):
    require(len(values) == 1, "portable source requires one actual " + label)
    return values[0]


def xy(value):
    return (scalar(value["x"]), scalar(value["y"]))


def alias(value):
    return value["$node"]["observation_key"]


def row_nodes(graph, value):
    fields = graph.fields(value)
    rows = fields["items"]
    require("n" not in fields or fields["n"] == len(rows), "portable source object-list count differs")
    return [graph.node(item if "$node" in item else item["o"]) for item in rows]


def creation_time(graph, header, native_id):
    logs = row_nodes(graph, graph.fields(header)["f20"])
    matches = [row for row in logs if row["fields"]["f48"] == native_id]
    require(len(matches) <= 1, "portable source origin creation event is ambiguous")
    events = [] if not matches else row_nodes(graph, matches[0]["identity"])
    return {"value": events[0]["fields"]["f18"] if events else 2592000, "actual_creation_event_present": bool(events)}


def selected_origin(graph, link, profile, sketch, external_index, points):
    root, header = link["root"], link["header"]
    origin = one([graph.node(value) for value in link["resolved_roots"] if value["class"] == "moOriginProfileFeature_c"], "origin profile")
    origin_id = origin["fields"]["f08"]
    external = graph.fields(points[external_index]["point"]["ext"], "sgExtEnt_c")
    wrapper = graph.fields(external["f08"], "moSketchExtRef_w")
    selected = graph.fields(wrapper["f58"], "moCompSketchEntHandle_c")
    component = graph.fields(selected["f58"], "moUnitComponent_c")
    time_value = creation_time(graph, header, origin_id)
    require(component["owner"]["$node"] == root and component["has_ext"] == 0,
            "portable source origin reference is owned by a foreign model")
    require(selected["ff0"] == {"f00": origin_id, "f08": time_value["value"]},
            "portable source origin reference has a foreign persistent identity or birth epoch")
    origin_sketch = graph.fields(origin["fields"]["pd_f80"], "sgSketch")
    require(graph.handle(selected["f0f8"], "sgPointHandle") == 0 and selected["f100"] == origin_sketch["points"][0]["point"]["f08"],
            "portable source external point lost its actual origin point")
    return {"name": graph.name(origin["identity"]), "native_id": origin_id, "creation_time": time_value,
            "profile": origin["identity"], "point_index": external_index, "component_owner": component["owner"]["$node"]}


def rectangle_geometry(graph, link):
    profile = one([graph.node(value) for value in link["resolved_roots"] if value["class"] == "moProfileFeature_c"], "ordinary profile")
    sketch_ref = profile["fields"]["pd_f80"]
    sketch = graph.fields(sketch_ref, "sgSketch")
    arrays = ("texts", "hatches", "arcs", "ellipses", "parabolas", "splines", "planes", "cylinders", "spheres", "cones", "parametric", "offsets", "sketch_offsets", "styled", "intersections", "tools", "blocks", "silhouettes")
    require(all(not sketch[name] for name in arrays), "portable origin child contains another geometry family")
    points, lines, dims = sketch["points"], sketch["lines"], sketch["dims"]
    require(sketch["npoints"] == len(points) and sketch["nlines"] == len(lines), "portable source geometry counts differ")
    require(all(not row["point"].get("has_name", 0) and row["point"].get("group") is None for row in points),
            "portable source contains authored point names or groups")
    for name in ("val_g1", "val_g3", "offset_dims", "log_g3", "iso", "linear_patterns", "linear_patt_cons", "circular_patterns", "circular_patt_cons", "list_7c0", "list_9f0", "groups"):
        require(not dims[name], "portable source has an unsupported dimension group: " + name)
    live, retired = [], []
    for index, row in enumerate(lines):
        fields = row["line"]
        require(not fields.get("has_name", 0) and fields.get("group") is None and fields.get("ext") is None,
                "portable source contains a named grouped or externally linked line")
        if fields["f54"] & 1:
            require(index == 0 and fields["f54"] == 5 and row["flags"] == fields["f08"] == fields["fd0"] == fields["f20"] == 0
                    and fields["f0c"] == -1 and fields["ext"] is None and fields["group"] is None,
                    "portable source has an unqualified retired line")
            retired.append(index)
        else:
            require(row["flags"] in (0, 2) and bool(fields["f54"] & 8) == (row["flags"] == 2), "portable source line construction markers disagree")
            live.append((index, row))
    boundary = [(index, row) for index, row in live if row["flags"] == 0]
    diagonals = [(index, row) for index, row in live if row["flags"] == 2]
    require(len(boundary) == 4 and len(diagonals) in (0, 2), "portable source is outside the corner or centered rectangle families")
    used = {endpoint(row["line"], key) for _, row in boundary for key in ("fc8", "fcc")}
    require(len(used) == 4 and all(0 <= value < len(points) for value in used), "portable source contour point ownership differs")
    positions = {index: xy(points[index]["point"]["pos"]) for index in used}
    xs = sorted({value[0] for value in positions.values()}); ys = sorted({value[1] for value in positions.values()})
    require(len(xs) == len(ys) == 2, "portable source contour is not axis aligned")
    vertices = [(xs[0], ys[0]), (xs[1], ys[0]), (xs[1], ys[1]), (xs[0], ys[1])]
    point_roles = [one([index for index, position in positions.items() if position == value], "actual rectangle corner") for value in vertices]
    line_roles, directions = [], []
    for index in range(4):
        endpoints = {point_roles[index], point_roles[(index + 1) % 4]}
        native_index, row = one([(i, row) for i, row in boundary if {endpoint(row["line"], key) for key in ("fc8", "fcc")} == endpoints], "actual rectangle edge")
        line_roles.append(native_index); directions.append(endpoint(row["line"], "fc8") == point_roles[index])
    axes = dims["log_g1"]
    require(dims["nlog1"] == len(axes) == 4, "portable source requires four complete axis relations")
    axis_roles = []
    for row in axes:
        value = row["d"]; check_drive(value)
        native_index = graph.handle(value["h1"], "sgLineHandle")
        require(native_index in line_roles, "portable source axis relation targets a noncontour line")
        role = line_roles.index(native_index)
        require(value["f80"] == (4 if role % 2 == 0 else 5), "portable source axis and real line direction disagree")
        axis_roles.append(role)
    require(sorted(axis_roles) == list(range(4)), "portable source axis ownership is duplicated")
    centered = bool(diagonals)
    external_index = one([index for index, row in enumerate(points) if row["kind"] == 1 and row["point"]["fe4"] == 6], "actual external origin point")
    local_index = one([index for index, row in enumerate(points) if index not in used and index != external_index], "actual local center") if centered else point_roles[0]
    require(len(points) == 5 + int(centered) and xy(points[external_index]["point"]["pos"]) == (0., 0.), "portable source has an extra or displaced point")
    require(xy(points[local_index]["point"]["pos"]) == (0., 0.), "portable source anchor is not at its actual origin")
    if centered:
        require(isclose(xs[0], -xs[1], abs_tol=1e-14) and isclose(ys[0], -ys[1], abs_tol=1e-14), "portable source centered contour is asymmetric")
    origin = selected_origin(graph, link, profile, sketch, external_index, points)
    binary_roles = check_binary(graph, dims, point_roles, line_roles, local_index, external_index, diagonals)
    drivers = read_drivers(graph, dims, sketch_ref, points, point_roles, vertices)
    return {"profile": profile["identity"], "native_id": profile["fields"]["f08"], "sketch": sketch_ref["$node"], "sketch_name": graph.name(profile["identity"]),
            "kind": "center-anchored" if centered else "corner-anchored", "vertices_m": vertices,
            "point_roles": point_roles, "line_roles": line_roles, "source_line_forward": directions,
            "axis_source_to_role": axis_roles, "binary_roles": binary_roles, "drivers": drivers,
            "origin": origin, "retired_line_rows": retired, "constraint_count": len(axes) + len(binary_roles) + len(drivers),
            "visible_line_count": len(live), "source_geometry_counts": {"points": len(points), "lines": len(lines)}}


def check_binary(graph, dims, point_roles, line_roles, local, external, diagonals):
    rows = dims["log_g2"]
    require(dims["nlog2"] == len(rows) == (3 if diagonals else 1), "portable source anchor relation count differs")
    found = []
    for row in rows:
        value = row["d"]; check_drive(value)
        require(value["f80"] == 9, "portable source has an unknown binary relation")
        first = graph.handle(value["h1"], "sgPointHandle")
        second_kind = value["h2"]["$node"]["class"]
        second = graph.handle(value["h2"], second_kind)
        if second_kind == "sgPointHandle":
            require({first, second} == {local, external}, "portable source anchor binds another point")
            found.append({"kind": "origin-coincident", "first": first, "second": second})
        else:
            require(second_kind == "sgLineHandle" and first == local and second in [index for index, _ in diagonals], "portable source center relation has another point or line")
            line = one([row["line"] for index, row in diagonals if index == second], "actual diagonal")
            ends = {endpoint(line, key) for key in ("fc8", "fcc")}
            role = one([index for index in (0, 1) if ends == {point_roles[index], point_roles[index + 2]}], "actual opposite-corner diagonal")
            found.append({"kind": "center-on-diagonal", "first": first, "line": second, "canonical_diagonal": role})
    require(sum(row["kind"] == "origin-coincident" for row in found) == 1, "portable source lacks exactly one origin coincidence")
    if diagonals:
        require(sorted(row["canonical_diagonal"] for row in found if row["kind"] == "center-on-diagonal") == [0, 1], "portable source center does not constrain both diagonals")
    require(not any(row.get("line") in line_roles for row in found), "portable source binary relation was assigned a contour line")
    return found


def read_drivers(graph, dims, sketch_ref, points, point_roles, vertices):
    rows = dims["val_g2"]
    displays = row_nodes(graph, dims["f118"])
    require(dims["ng2"] == len(rows) == len(displays) == 2, "portable source requires two actual driving lengths and displays")
    result = []
    for index, row in enumerate(rows):
        value_node = graph.node(row["d"], "sgPntPntDist"); value = value_node["fields"]; check_drive(value)
        require(value["f80"] == value["f180"] == value["f184"] == value["f1b8"] == 1 and value["f1bc"] == value["fa0"] == 0 and value["plane"] is None,
                "portable source distance is projected or not ordinary point distance")
        require(all(scalar(value["dir"][key]) == 0 for key in ("x", "y", "z")), "portable source distance has an authored projection")
        selected = [graph.handle(value[key], "sgPointHandle") for key in ("h1", "h2")]
        require(selected == point_roles[index:index + 2], "portable source driving distance selects a different ordered rectangle side")
        parameter = graph.node(value["f28"], "moLengthParameter_c"); fields = parameter["fields"]
        length = scalar(fields["f58"])
        require(length > 0 and fields["f48"] is None and fields["f68"] == 0, "portable source length has an expression or alternative value")
        expected = vertices[index + 1][index] - vertices[index][index]
        require(isclose(length, expected, rel_tol=1e-12, abs_tol=1e-14), "portable source live length differs from its actual points")
        display = displays[index]; handles = display["fields"]["f850"]
        require(display["identity"]["class"] == "moDisplayDistanceDim_c" and len(handles) == display["fields"]["n850"] == 1, "portable source driving display ownership differs")
        handle = graph.fields(handles[0]["o"], "moSkDimHandleValG2_c")
        require(handle["ff0"]["$node"] == sketch_ref["$node"] and handle["ff8"] == index, "portable source display targets another sketch or value")
        text = display["fields"]["f6a0"]
        text_xyz = [scalar(text["f38"][key]) for key in ("x", "y", "z")]
        require(not graph.text(text["f08"]) and all(not graph.text(display["fields"][key]) for key in ("f7f8", "f800", "f808", "f810", "f818", "f820")),
                "portable source dimension has authored text or a prefix or suffix outside this constructor")
        result.append({"name": graph.name(parameter["identity"]), "length_m": length, "source_point_indices": selected,
                       "text_m": xy(text["f38"]) if text_xyz[2] == 0. else None, "text_xyz_m": text_xyz,
                       "constructor_text_representable": text_xyz[2] == 0., "value": value_node["identity"], "parameter": parameter["identity"],
                       "display": display["identity"], "route_centerline": bool(display["fields"]["f1014"] & 0x800)})
    require(result[0]["name"].casefold() != result[1]["name"].casefold() and result[0]["route_centerline"] == result[1]["route_centerline"],
            "portable source dimension names or routing cannot be represented by this constructor")
    return result
