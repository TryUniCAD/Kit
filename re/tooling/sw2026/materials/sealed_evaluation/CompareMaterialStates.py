from collections import Counter
from math import isclose, isfinite
from pathlib import PureWindowsPath


FEATURES = (("Front Plane", "RefPlane"), ("Top Plane", "RefPlane"), ("Right Plane", "RefPlane"),
            ("Origin", "OriginProfileFeature"), ("AnchorSketch", "ProfileFeature"), ("AnchorBoss", "Extrusion"))
FEATURE_SET = {name for name, _ in FEATURES}
DRIVERS = ("D1@AnchorSketch", "D2@AnchorSketch", "D1@AnchorBoss")
PHASE_COMPARE = {
    "cold": ("Swap", "after_save", "initial"), "rebuilt": ("Swap", "after_save", "initial"),
    "edited": ("Depth", "changed", "depth_edit"), "after_save": ("Depth", "after_save", "depth_edit"),
    "fresh_reopen": ("Reopen", "before", "depth_edit"), "fresh_rebuild": ("Reopen", "after_save", "depth_edit"),
}


def require(value, message):
    if not value:
        raise ValueError(message)


def close(actual, want, *, absolute=1e-12):
    require(type(actual) in (float, int) and type(want) in (float, int)
            and isfinite(actual) and isfinite(want) and isclose(actual, want, rel_tol=2e-7, abs_tol=absolute),
            "physical value differs from its selected intent or locked native source")


def canonical_names(value):
    return PureWindowsPath(value["database"]).stem.casefold(), value["material"]


def named_tree(rows):
    ordered = []
    for row in rows:
        require(row["error"] == 0 and row["warning"] is False, "feature tree has a native diagnostic")
        if row["name"] in FEATURE_SET:
            require(row["suppressed"] is False, "actual modeled feature is suppressed")
            ordered.append((row["name"], row["type"], row["parent"]))
    expected = [(name, kind, None) for name, kind in FEATURES]
    require(ordered == expected, "ordered named planes origin sketch and boss differ")
    return ordered


def match_segments(rows, family, bounds):
    low, high = bounds
    points = ((low[0], low[1]), (high[0], low[1]), (high[0], high[1]), (low[0], high[1]))
    expected = [("edge" + str(i), False, points[i], points[(i + 1) % 4]) for i in range(4)]
    if family == "center":
        expected += [("diagonal" + str(i), True, points[i], points[i + 2]) for i in range(2)]
    require(len(rows) == len(expected), "native sketch carries extra or missing construction or contour geometry")
    roles = {}
    for row in rows:
        require(row["kind"] == "line" and len(row["start"]) == len(row["end"]) == 2,
                "native sketch has nonline geometry or an invalid endpoint")
        matching = []
        for label, construction, start, end in expected:
            if row["construction"] is not construction:
                continue
            for left, right in ((start, end), (end, start)):
                if all(isfinite(value) and abs(value - target) < 1e-10 for actual, pair in (
                    (row["start"], left), (row["end"], right)
                ) for value, target in zip(actual, pair, strict=True)):
                    matching.append(label)
        require(len(matching) == 1 and matching[0] not in roles, "native geometry does not bind a unique intended edge")
        roles[matching[0]] = row
    require(len(roles) == len(expected), "native rectangle geometry is incomplete")
    return roles


def relation_counts(rows, family):
    expected = Counter({(1, (2, 2)): 2, (4, (3,)): 2, (5, (3,)): 2, (9, (2, 2)): 1})
    if family == "center":
        expected[9, (2, 3)] = 2
    require(all(row["suppressed"] is False and len(row["entity_ids"]) == len(row["entity_types"])
                for row in rows), "native sketch has an invalid or suppressed relation")
    actual = Counter((row["kind"], tuple(sorted(row["entity_types"]))) for row in rows)
    require(actual == expected, "native sketch relation types or counts differ from the exact anchor profile")
    return actual


def check_source_observation(state, expected, family):
    rectangle = state["rectangle"]
    require(state["configuration"] == expected["configuration"] and rectangle["body_count"] == expected["solid_body_count"] == 1
            and rectangle["constraint_status"] == 3 and not state["legacy_mass"]["override_mass"]
            and state["body_material"] == {"database": "", "material": ""} and not state["body_material_id_name"]
            and canonical_names(state["part_material"]) == canonical_names(expected["part_material"]),
            "locked source does not represent the selected ordinary physical material intent")
    require(set(rectangle["dimensions_m"]) == set(DRIVERS), "locked source lost an actual named driving dimension")
    for name in DRIVERS:
        close(rectangle["dimensions_m"][name], expected["dimensions_m"][name])
    actual = state["mass"]
    geometry = expected["geometry"]
    require(actual["use_system_units"] is True, "locked selected-body mass did not use SI")
    close(actual["mass"], expected["mass_kg"], absolute=1e-14)
    close(actual["density"], expected["density_kg_m3"])
    close(actual["volume"], geometry["volume"], absolute=1e-16)
    close(rectangle["mass_properties"]["area"], geometry["area"])
    for actual, want in zip(rectangle["mass_properties"]["com"], geometry["com"], strict=True):
        close(actual, want)
    named_tree(rectangle["tree"])
    match_segments(rectangle["geometry"], family, geometry["bounds"])
    relation_counts(rectangle["relations"], family)


def check_generated_observation(measured, anchor, prior, expected, family, label):
    require(measured["body_count"] == 1 and measured["matches_requested_identity"]
            and measured["matches_requested_density"] and measured["matches_requested_mass"]
            and canonical_names(measured["material"]) == canonical_names(prior["part_material"])
            and not measured["body_id_name"] and not measured["mass_properties"]["override_mass"],
            "candidate does not preserve the source part assignment or scoped physical mass")
    source = prior["rectangle"]
    require(named_tree(measured["tree"]) == named_tree(source["tree"])
            and anchor["constraint_status"] in ((1, 3) if label == "cold" else (3,))
            and anchor["origin_binding_verified"] is True,
            "candidate does not retain the named feature graph and constrained origin")
    require(set(measured["drivers_m"]) == set(DRIVERS), "candidate lost an actual native driving dimension")
    for name in DRIVERS:
        close(measured["drivers_m"][name], source["dimensions_m"][name])
    physical = measured["selected_mass_properties"]
    source_physical = prior["mass"]
    require(physical["use_system_units"] is True, "candidate selected-body mass did not use SI")
    close(physical["density"], source_physical["density"])
    close(physical["mass"], source_physical["mass"], absolute=1e-14)
    close(physical["volume"], source_physical["volume"], absolute=1e-16)
    close(measured["mass_properties"]["area"], source["mass_properties"]["area"])
    for actual, want in zip(measured["mass_properties"]["com"], source["mass_properties"]["com"], strict=True):
        close(actual, want)
    for actual, want in zip(anchor["bounds"], expected["geometry"]["bounds"], strict=True):
        for left, right in zip(actual, want, strict=True):
            close(left, right)
    generated_roles = match_segments(anchor["geometry"], family, expected["geometry"]["bounds"])
    source_roles = match_segments(source["geometry"], family, expected["geometry"]["bounds"])
    require(generated_roles.keys() == source_roles.keys()
            and relation_counts(anchor["relations"], family) == relation_counts(source["relations"], family),
            "candidate and locked native source topology differ")


def bounds(author, body, swapp):
    extrema = [[], []]
    for axis in range(3):
        for index, sign in enumerate((-1.0, 1.0)):
            direction = [0.0] * 3
            direction[axis] = sign
            outputs = [swapp.VARIANT(swapp.pythoncom.VT_BYREF | swapp.pythoncom.VT_R8, 0.0) for _ in range(3)]
            reply = author.get(body, "GetExtremePoint", *direction, *outputs)
            if isinstance(reply, tuple):
                require(len(reply) == 4 and bool(reply[0]), "typed native extremum did not return coordinates")
                value = reply[axis + 1]
            else:
                require(bool(reply), "native solid extremum could not be measured")
                value = outputs[axis].value
            extrema[index].append(float(value))
    return extrema


def owner_bindings(author, family, roles):
    model = author.model
    author.get(model, "ClearSelection2", True)
    try:
        extension = author.get(model, "Extension")
        require(author.get(extension, "SelectByID2", "Point1@Origin", "EXTSKETCHPOINT",
                           0.0, 0.0, 0.0, False, 0, author.sw.nothing(), 0),
                "actual document Origin point could not be selected")
        selected = author.get(author.get(model, "SelectionManager"), "GetSelectedObject6", 1, -1)
        origin = author.typed(selected, "SketchPoint")
        manager = author.get(author.sketch, "RelationManager")
        coincidence = []
        side_relations = []
        for relation in author.get(manager, "GetRelations", 0) or ():
            if int(author.get(relation, "GetRelationType")) != 9:
                continue
            kinds = list(author.get(relation, "GetEntitiesType") or ())
            entries = list(author.get(relation, "GetEntities") or ())
            require(len(kinds) == len(entries) == 2, "native coincidence has incomplete participants")
            if kinds == [2, 2]:
                matches = [int(author.get(author.app, "IsSame", origin, entity)) == 1 for entity in entries]
                require(matches.count(True) == 1, "native coincidence does not reference the actual document Origin")
                coincidence.append(entries[matches.index(False)])
            else:
                require(sorted(kinds) == [2, 3], "native center relation has the wrong concrete owners")
                side_relations.append((entries[kinds.index(2)], entries[kinds.index(3)]))
        require(len(coincidence) == 1, "native rectangle requires exactly one actual Origin coincidence")
        point = author.typed(coincidence[0], "SketchPoint")
        require(int(author.get(author.app, "IsSame", author.sketch, author.get(point, "GetSketch"))) == 1,
                "native origin coincidence lost its actual local sketch point")
        require(all(abs(value) < 1e-10 for value in author.point(point)), "coincident local point moved from the origin")
        if family == "center":
            actual = [tuple(author.get(line, "GetID")) for _, line in side_relations]
            expected = [tuple(roles[name]["id"]) for name in ("diagonal0", "diagonal1")]
            require(Counter(actual) == Counter(expected) and
                    all(int(author.get(author.app, "IsSame", point, center)) == 1 for center, _ in side_relations),
                    "native center point does not own both actual construction diagonals")
        else:
            bottom = roles["edge0"]
            point_id = tuple(author.get(point, "GetID"))
            require(any(tuple(bottom["point_bindings"][end]["id"]) == point_id
                        and all(abs(value) < 1e-10 for value in bottom[end]) for end in ("start", "end"))
                    and not side_relations, "native corner origin coincidence does not select the lower contour corner")
    finally:
        author.get(model, "ClearSelection2", True)


def observe_anchor(author, expected, family, swapp):
    profile = author.get(author.model, "FeatureByName", "AnchorSketch")
    boss = author.get(author.model, "FeatureByName", "AnchorBoss")
    require(profile is not None and boss is not None, "native document lost its sketch or boss")
    sketch_parents = {str(author.get(node, "Name")) for node in author.get(profile, "GetParents") or ()}
    boss_parents = {str(author.get(node, "Name")) for node in author.get(boss, "GetParents") or ()}
    require("Front Plane" in sketch_parents and {"AnchorSketch", "Front Plane"} <= boss_parents,
            "native features do not retain their actual Front Plane and profile references")
    author.sketch = author.get(profile, "GetSpecificFeature2")
    geometry = author.geometry()
    roles = match_segments(geometry, family, expected["geometry"]["bounds"])
    relations = author.relation_graph()
    relation_counts(relations, family)
    owner_bindings(author, family, roles)
    part = author.typed(author.model, "PartDoc")
    bodies = author.get(part, "GetBodies2", 0, False) or ()
    require(len(bodies) == 1, "native extrema require one real solid")
    body = author.typed(bodies[0], "Body2")
    require(author.get(body, "GetType") == 0, "extrema owner is not a solid")
    return {"geometry": geometry, "relations": relations, "constraint_status": int(author.get(author.sketch, "GetConstrainedStatus")),
            "bounds": bounds(author, body, swapp), "origin_binding_verified": True}
