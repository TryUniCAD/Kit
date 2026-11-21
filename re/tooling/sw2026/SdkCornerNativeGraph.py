from __future__ import annotations

from collections import Counter
from math import isclose, isfinite

from AuthorCurves import require


def close(actual, expected):
    return type(actual) in (int, float) and type(expected) in (int, float) and isfinite(actual) and isfinite(expected) and isclose(actual, expected, rel_tol=2e-7, abs_tol=1e-12)


def short_name(full_name):
    pieces = full_name.split("@")
    require(len(pieces) >= 3 and all(pieces[:2]), "native dimension has no explicit feature owner")
    return "@".join(pieces[:2])


def id_pair(value):
    require(type(value) is list and len(value) == 2 and all(type(item) is int for item in value),
            "native entity identity requires the two actual GetID components")
    return tuple(value)


def geometry_roles(geometry, vertices):
    require(len(geometry) == len(vertices) == 4 and all(row["kind"] == "line" and not row["construction"] for row in geometry),
            "native rectangle must contain exactly four ordinary lines")
    line_ids, point_ids = [], [None] * 4
    for index, (first, last) in enumerate(zip(vertices, vertices[1:] + vertices[:1], strict=True)):
        matches = []
        for row in geometry:
            forward = all(close(a, b) for a, b in zip((*row["start"], *row["end"]), (*first, *last), strict=True))
            reverse = all(close(a, b) for a, b in zip((*row["end"], *row["start"]), (*first, *last), strict=True))
            if forward or reverse:
                matches.append((row, forward))
        require(len(matches) == 1, "native rectangle has a missing or ambiguous authored edge")
        row, forward = matches[0]
        line_ids.append(id_pair(row["id"]))
        endpoints = row["point_bindings"]
        for ordinal, side in ((index, "start" if forward else "end"), ((index + 1) % 4, "end" if forward else "start")):
            observed = id_pair(endpoints[side]["id"])
            require(point_ids[ordinal] in (None, observed), "adjacent native rectangle lines do not share the same actual point identity")
            point_ids[ordinal] = observed
    require(len(set(line_ids)) == len(set(point_ids)) == 4, "native rectangle entity identities are not independent")
    return {"line_ids": [list(value) for value in line_ids], "point_ids": [list(value) for value in point_ids]}


def ordered_points(geometry, roles):
    require(len(geometry) == 4, "native rectangle gained or lost an entity")
    by_line = {id_pair(row["id"]): row for row in geometry}
    require(len(by_line) == 4 and set(by_line) == {id_pair(value) for value in roles["line_ids"]},
            "native edit changed the actual four segment identities")
    positions = {}
    for index, line_id in enumerate(roles["line_ids"]):
        row = by_line[id_pair(line_id)]
        require(row["kind"] == "line" and not row["construction"], "native edit changed an ordinary line kind")
        endpoints = row["point_bindings"]
        actual = {id_pair(endpoints[side]["id"]): tuple(row[side]) for side in ("start", "end")}
        expected = {id_pair(roles["point_ids"][index]), id_pair(roles["point_ids"][(index + 1) % 4])}
        require(len(actual) == 2 and set(actual) == expected, "native edit changed the owned line endpoints")
        for point_id, position in actual.items():
            require(point_id not in positions or all(close(a, b) for a, b in zip(position, positions[point_id], strict=True)),
                    "shared native point identity has inconsistent coordinates")
            positions[point_id] = position
    return [list(positions[id_pair(value)]) for value in roles["point_ids"]]


def relation_signature(rows):
    result = []
    for row in rows:
        require(not row["suppressed"] and len(row["entity_types"]) == len(row["entity_ids"]),
                "native rectangle has suppressed or incomplete relation owners")
        entities = tuple(sorted((int(kind), id_pair(value)) for kind, value in zip(row["entity_types"], row["entity_ids"], strict=True)))
        result.append((row["kind"], entities, row["dimension"]["short_name"] if row["dimension"] else None))
    return sorted(result)


def verify_relations(rows, roles, parameter_names, values):
    expected, actual = Counter(), Counter()
    for index, line_id in enumerate(roles["line_ids"]):
        expected[(4 if index % 2 == 0 else 5, (id_pair(line_id),), None)] += 1
    for index, parameter_name in enumerate(parameter_names[:2]):
        endpoints = tuple(sorted(id_pair(value) for value in roles["point_ids"][index:index + 2]))
        expected[(1, endpoints, parameter_name)] += 1
    anchors = []
    for row in rows:
        require(not row["suppressed"], "anchored rectangle has a suppressed relation")
        dimension = row["dimension"]
        if row["kind"] == 9:
            require(dimension is None and sorted(row["origin_matches"]) == [False, True] and
                    row["entity_types"] == [2, 2], "coincidence must target the selected actual model origin and one local point")
            local, = [entity for entity, is_origin in zip(row["entity_ids"], row["origin_matches"], strict=True) if not is_origin]
            require(id_pair(local) == id_pair(roles["point_ids"][0]), "coincidence targets a different local contour corner")
            anchors.append(row)
            continue
        owner = dimension["short_name"] if dimension is not None else None
        actual[(row["kind"], tuple(sorted(id_pair(value) for value in row["entity_ids"])), owner)] += 1
        if row["kind"] == 1:
            require(dimension is not None and dimension["driving"] and close(dimension["value_m"], values[owner]),
                    "relation lost its actual editable named driving dimension")
        else:
            require(dimension is None, "unary relation acquired an unexpected display dimension")
    require(len(rows) == 7 and len(anchors) == 1 and actual == expected,
            "native origin rectangle relation kinds or actual entity owners differ")


def verify_state(author, state, case, tree, parameters, *, roles, rebuilt):
    require([[row["name"], row["type"], row["parent"]] for row in state["tree"]] == tree and
            not any(row["suppressed"] or row["error"] or row["warning"] for row in state["tree"]),
            "anchored rectangle complete ordered tree differs or reports diagnostics")
    require(state["configuration"] == case["configuration_name"] and case["support"] in state["sketch_parents"] and
            case["profile"] in state["boss_parents"] and case["support"] in state["boss_parents"],
            "anchored rectangle lost active configuration or actual support and profile dependencies")
    require(state["whats_wrong"] == 0 and state["body_count"] == 1,
            "anchored rectangle has diagnostics or lacks its single solid")
    require(state["constraint_status"] == 3 if rebuilt else state["constraint_status"] in (1, 3),
            "origin rectangle must be fully constrained after native rebuild")
    width, height, depth = (parameters[name] for name in case["parameter_names"])
    for name in case["parameter_names"]:
        value = state["dimensions"][name]
        require(value["short_name"] == name and value["driving"], "native parameter lost its feature owner or driving state")
        author.rec.close_number(name, value["value_m"], parameters[name])
    vertices = ordered_points(state["geometry"], roles)
    expected = [[0.0, 0.0], [width, 0.0], [width, height], [0.0, height]]
    for actual, intended in zip(vertices, expected, strict=True):
        for observed, want in zip(actual, intended, strict=True):
            author.rec.close_number("origin preserved rectangle corner", observed, want)
    mass = state["mass"]
    author.rec.close_number("anchored volume", mass["volume"], width * height * depth, absolute=1e-16)
    author.rec.close_number("anchored area", mass["area"], 2 * (width * height + width * depth + height * depth), absolute=1e-16)
    author.rec.close_number("anchored mass", mass["mass"], width * height * depth * case["density_kg_m3"], absolute=1e-16)
    for actual, target in zip(mass["com"], (width / 2, height / 2, depth / 2), strict=True):
        author.rec.close_number("anchored prism centre", actual, target)
    verify_relations(state["relations"], roles, case["parameter_names"], parameters)
    return relation_signature(state["relations"])
