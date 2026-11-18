from __future__ import annotations

from math import isclose

from AuthorCurves import require


def position_child(author, model, case):
    width, height, _ = case["child_size_m"]
    feature = author.get(model, "FeatureByName", "Sketch1")
    require(feature is not None and author.get(feature, "GetTypeName2") == "ProfileFeature", "the source seed has no ordinary named sketch")
    author.get(model, "ClearSelection2", True)
    require(bool(author.get(feature, "Select2", False, 0)), "the child sketch could not be selected for explicit placement")
    author.get(model, "EditSketch")
    manager = author.get(model, "SketchManager")
    sketch = author.get(manager, "ActiveSketch")
    require(sketch is not None and int(author.get(sketch, "GetConstrainedStatus")) == 2, "the seed must expose its two unanchored translation freedoms")
    segments = author.get(sketch, "GetSketchSegments") or ()
    require(len(segments) == 4 and all(not author.get(row, "ConstructionGeometry") for row in segments), "explicit source positioning requires four ordinary line edges")
    points = {}
    for segment in segments:
        line = author.typed(segment, "SketchLine")
        for field in ("GetStartPoint2", "GetEndPoint2"):
            point = author.typed(author.get(line, field), "SketchPoint")
            points[tuple(author.get(point, "GetID"))] = point
    require(len(points) == 4, "the ordinary rectangle has ambiguous native point ownership")
    before = {key: author.point(point) for key, point in points.items()}
    left = min(position[0] for position in before.values())
    bottom = min(position[1] for position in before.values())
    corners = [
        key for key, position in before.items()
        if isclose(position[0], left, rel_tol=0.0, abs_tol=1e-10)
        and isclose(position[1], bottom, rel_tol=0.0, abs_tol=1e-10)
    ]
    require(len(corners) == 1, "the native rectangle has no unique lower-left point")
    key, = corners
    point = points[key]
    target = [-width / 2, -height / 2, 0.0]
    require(bool(author.get(point, "SetCoords", *target)), "the native point setter refused the authored sketch location")
    expected = [(-width / 2, -height / 2, 0.0), (width / 2, -height / 2, 0.0),
                (width / 2, height / 2, 0.0), (-width / 2, height / 2, 0.0)]
    after = {str(key): author.point(point) for key, point in points.items()}
    for actual in after.values():
        matches = [row for row in expected if all(isclose(a, b, rel_tol=0.0, abs_tol=1e-10) for a, b in zip(actual, row, strict=True))]
        require(len(matches) == 1, "the positioned native sketch differs from its independently authored rectangle")
        expected.remove(matches[0])
    author.rec.data["explicit_child_sketch_position"] = {"selected_native_point_id": list(key), "requested_local_m": target,
                                                         "before": {str(index): value for index, value in before.items()},
                                                         "after": after, "empirical_centroid_correction": False}
    author.rec.flush()
    author.get(model, "ClearSelection2", True)
    author.get(manager, "InsertSketch", True)
    require(bool(author.get(model, "ForceRebuild3", False)), "the explicitly positioned source child failed rebuild")
