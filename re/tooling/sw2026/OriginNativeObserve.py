from __future__ import annotations

from collections import Counter
from math import isclose
from pathlib import Path

from AuthorCurves import require
from AuthorDrawingSources import compare_states, snapshot as drawing_snapshot
from AuthorRectangleAnchors import RectangleAuthor
from OriginNativePredict import dimensions, predict, vertices


def pair(value):
    require(isinstance(value, (list, tuple)) and len(value) == 2 and all(type(x) is int for x in value), "native geometry identity must have two integer components")
    return tuple(value)


def same(first, second):
    return len(first) == len(second) and all(isclose(a, b, rel_tol=2e-7, abs_tol=1e-10) for a, b in zip(first, second, strict=True))


def geometry_roles(author, geometry, case, edited):
    wanted = vertices(case, edited)
    contour = [row for row in geometry if not row["construction"]]
    diagonal = [row for row in geometry if row["construction"]]
    require(len(contour) == 4 and len(diagonal) == (2 if case["kind"] == "center" else 0) and all(row["kind"] == "line" for row in geometry), "native child lost its complete contour or construction segments")
    line_ids, point_ids = [], [None] * 4
    for index, (start, end) in enumerate(zip(wanted, wanted[1:] + wanted[:1], strict=True)):
        matches = [(row, forward) for row in contour for forward in (True, False)
                   if same(row["start" if forward else "end"], start) and same(row["end" if forward else "start"], end)]
        require(len(matches) == 1, "native rectangle edge is missing or ambiguous")
        row, forward = matches[0]
        line_ids.append(pair(row["id"]))
        for slot, side in ((index, "start" if forward else "end"), ((index + 1) % 4, "end" if forward else "start")):
            identity = pair(row["point_bindings"][side]["id"])
            require(point_ids[slot] in (None, identity), "adjacent native edges lost the actual shared point")
            point_ids[slot] = identity
        for actual, target in zip((row["start"], row["end"]), (start, end) if forward else (end, start), strict=True):
            for value, expected in zip(actual, target, strict=True):
                author.rec.close_number("actual authored corner", value, expected)
    diagonal_ids = []
    for index in range(len(diagonal)):
        matches = [row for row in diagonal if (same(row["start"], wanted[index]) and same(row["end"], wanted[index + 2]))
                   or (same(row["end"], wanted[index]) and same(row["start"], wanted[index + 2]))]
        require(len(matches) == 1, "native construction diagonal lost its actual opposite corners")
        diagonal_ids.append(pair(matches[0]["id"]))
    return {"line_ids": line_ids, "point_ids": point_ids, "diagonal_ids": diagonal_ids}


def relation_roles(rows, roles, centered):
    require(len(rows) == (9 if centered else 7) and all(not row["suppressed"] for row in rows), "native child lost complete active relation count")
    axes = [row for row in rows if row["kind"] in (4, 5)]
    require(len(axes) == 4 and all(len(row["entity_ids"]) == len(row["entity_types"]) == 1 for row in axes), "native axis constraints lost unary ownership")
    line_types = {row["entity_types"][0] for row in axes}
    require(len(line_types) == 1 and 2 not in line_types, "native line relation entities do not have one distinct line kind")
    line_type, = line_types
    actual = Counter((row["kind"], tuple(pair(x) for x in row["entity_ids"])) for row in axes)
    require(actual == Counter((4 if index % 2 == 0 else 5, (identity,)) for index, identity in enumerate(roles["line_ids"])), "horizontal or vertical constraint targets differ")
    distances = [row for row in rows if row["kind"] == 1]
    require(len(distances) == 2 and all(row["entity_types"] == [2, 2] for row in distances), "native driving distances lost two actual point owners")
    require(Counter(tuple(sorted(pair(x) for x in row["entity_ids"])) for row in distances)
            == Counter(tuple(sorted(roles["point_ids"][index:index + 2])) for index in range(2)), "native length dimensions target different endpoints")
    coincidences = [row for row in rows if row["kind"] == 9]
    require(len(axes) + len(distances) + len(coincidences) == len(rows), "native child gained an unrelated relation kind")
    if centered:
        point_lines = [row for row in coincidences if sorted(row["entity_types"]) == sorted((2, line_type))]
        require(len(point_lines) == 2, "centered child lost its two point on diagonal relations")
        centers, lines = [], []
        for row in point_lines:
            centers.extend(pair(value) for kind, value in zip(row["entity_types"], row["entity_ids"], strict=True) if kind == 2)
            lines.extend(pair(value) for kind, value in zip(row["entity_types"], row["entity_ids"], strict=True) if kind == line_type)
        require(len(set(centers)) == 1 and set(lines) == set(roles["diagonal_ids"]), "center relations do not share the same local center and actual diagonals")
        local = centers[0]
    else:
        local = roles["point_ids"][0]
    point_points = [row for row in coincidences if row["entity_types"] == [2, 2]]
    require(len(point_points) == 1, "origin anchor lost its separate point to point relation")
    identities = [pair(value) for value in point_points[0]["entity_ids"]]
    require(identities.count(local) == 1 and len(set(identities)) == 2, "origin coincidence lost its actual local point")
    external, = [value for value in identities if value != local]
    require(external not in roles["point_ids"] and (not centered or local not in roles["point_ids"]), "origin reference became an ordinary contour point")
    return {**roles, "local_anchor_id": local, "external_point_id": external}


def anchor_locations(author, roles):
    points = {}
    manager = author.get(author.sketch, "RelationManager")
    for relation in author.get(manager, "GetRelations", 0) or ():
        entities = list(author.get(relation, "GetEntities") or ())
        types = list(author.get(relation, "GetEntitiesType") or ())
        require(len(entities) == len(types), "native relation points are incomplete")
        for entity, kind in zip(entities, types, strict=True):
            if kind != 2:
                continue
            identity = pair(author.get(entity, "GetID"))
            position = author.point(entity)
            require(identity not in points or same(position, points[identity]), "actual point identity has inconsistent coordinates")
            points[identity] = position
    wanted = (roles["local_anchor_id"], roles["external_point_id"])
    require(all(identity in points for identity in wanted), "actual anchor points were not measured")
    for identity in wanted:
        for value in points[identity]:
            author.rec.close_number("actual anchor point at origin", value, 0.)
    return [{"id": list(identity), "position_m": points[identity]} for identity in wanted]


def child_state(author, child, case, edited, initial=False):
    saved = author.model, author.sketch
    try:
        author.model = child
        feature = author.get(child, "FeatureByName", case["sketch_name"])
        require(feature is not None, "actual child sketch feature is absent")
        author.sketch = author.get(feature, "GetSpecificFeature2")
        status = int(author.get(author.sketch, "GetConstrainedStatus"))
        require(status in ((1, 3) if initial else (3,)), "native child is not fully constrained after rebuild")
        geometry = author.geometry()
        roles = geometry_roles(author, geometry, case, edited)
        relations = author.relation_graph()
        roles = relation_roles(relations, roles, case["kind"] == "center")
        anchors = anchor_locations(author, roles)
        values = dimensions(case, edited)
        parameters = {}
        for name, key in zip(case["parameter_names"], ("width_m", "height_m", "depth_m"), strict=True):
            parameter = author.get(child, "Parameter", name)
            require(parameter is not None and author.get(parameter, "DrivenState") == 2 and not author.get(parameter, "ReadOnly"), "child dimension lost its actual driving owner")
            measured = float(author.get(parameter, "SystemValue"))
            author.rec.close_number(name, measured, values[key])
            parameters[name] = measured
        tree = author.feature_tree(required_names=(case["sketch_name"], case["boss_name"], case["origin_name"]))
        require([[row["name"], row["type"], row["parent"]] for row in tree] == case["part_tree"], "complete ordered child tree differs from authored prediction")
        require(all(not row["suppressed"] for row in tree), "native child tree contains a suppressed feature")
        ids = {}
        for label, name in (("origin", case["origin_name"]), ("ordinary_profile", case["sketch_name"])):
            value = author.get(author.get(child, "FeatureByName", name), "GetID")
            require(type(value) is int and value >= 0, "native profile has no real persistent identity")
            ids[label] = value
        require(ids["origin"] != ids["ordinary_profile"], "origin and ordinary profile are not distinct")
        part_doc = author.typed(child, "PartDoc")
        require(len(author.get(part_doc, "GetBodies2", 0, True) or ()) == 1, "child does not have its analytic single solid")
        require(author.get(author.get(child, "Extension"), "GetWhatsWrongCount") == 0, "child reports rebuild diagnostics")
        mass = author.rec.call("measure actual linked child", author.sw.mass, child)
        expected = predict(case, edited)["view"]
        for key, expected_key in (("volume", "child_volume_m3"), ("area", "child_area_m2")):
            author.rec.close_number(key, mass[key], expected[expected_key], absolute=1e-16)
        author.rec.close_number("child mass", mass["mass"], expected["child_volume_m3"] * case["density_kg_m3"], absolute=1e-16)
        for value, wanted in zip(mass["com"], expected["child_center_m"], strict=True):
            author.rec.close_number("child center", value, wanted)
        return {"geometry": geometry, "relations": relations, "entity_roles": roles, "profile_ids": ids,
                "dimensions": parameters, "tree": tree, "constraint_status": status, "mass": mass, "anchor_positions": anchors}
    finally:
        author.model, author.sketch = saved


def observe(author, model, case, native_path, edited, moved, initial=False):
    author.model = model
    require(Path(author.get(model, "GetPathName")).samefile(native_path), "native drawing resolved a different input file")
    drawing = author.typed(model, "DrawingDoc")
    wanted = predict(case, edited, moved)
    request = {"orientation": wanted["view"]["orientation"], "position_m": wanted["view"]["position_m"], "scale": wanted["view"]["scale"]}
    state = drawing_snapshot(author, model, drawing, request, Path(case["paths"]["child"]), 0)
    author.rec.data.setdefault("origin_drawing_observations", []).append({
        "native_path": str(native_path), "edited_child": edited, "moved_view": moved, "initial_observation": initial,
        "actual": state, "expected": wanted,
        "projection_policy": "preserve the constructed model-to-view frame; project the actual edited child bounds; translate the frame only by the declared view move",
        "post_rebuild_frame_preservation_previously_qualified": False,
    })
    author.rec.flush()
    compare_states(author, state, wanted)
    require(state["view"]["name"] == wanted["view"]["name"], "native view changed its authored feature identity")
    tree = author.feature_tree(required_names=())
    require([[row["name"], row["type"], row["parent"]] for row in tree] == case["drawing_tree"], "complete drawing tree differs from authored prediction")
    sheet_view = author.typed(author.get(drawing, "GetFirstView"), "View")
    view = author.typed(author.get(sheet_view, "GetNextView"), "View")
    child = author.get(view, "ReferencedDocument")
    return {"drawing": state, "drawing_tree": tree, "child": child_state(author, child, case, edited, initial),
            "actual_native_child_path": str(author.get(child, "GetPathName")), "display_selection_requires_typed_join": True}
