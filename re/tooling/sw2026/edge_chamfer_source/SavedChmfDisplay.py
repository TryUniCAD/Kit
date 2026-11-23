from math import dist, isclose

from convert.adapters.solidworks.Archive.Construction.Chamfers.Views.ChmfViewInput import ChmfViewInput
from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import ReadRigidXform
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import AnnoViewInput, KNoAnno
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.CheckChmfDist import ChmfViewPoint
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import CheckTreeAlias
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


def frame(fields):
    matrix, origin = ReadRigidXform(fields)
    return tuple(matrix[index::3] for index in range(3)), origin


def points(node, keys):
    return {key: ChmfViewPoint(node, key) for key in keys}


def read_intent(link, owners):
    assert owners.ModeWord == 1
    root = link.ConfigValue.RootValue.FieldsValue
    catalog = RequireNative(root["fa48"], "suObList").FieldsValue
    views = tuple(RequireNative(row["o"], "moAnnotationView_c") for row in catalog["items"])
    assert catalog["n"] == len(views) and root["feb0"] == KNoAnno + len(views)
    assert root["feb4"] == KNoAnno and root["nec8"] == len(root["fec0"]) == 1
    assert root["fec0"][0]["v"] == KNoAnno
    CheckTreeAlias(link, views)
    ordered = {}
    for index, node in enumerate(views, start=KNoAnno + 1):
        fields = node.FieldsValue
        basis, origin = frame(fields["f368"])
        assert fields["f360"] == index and origin == (0.0, 0.0, 0.0)
        ordered[index] = AnnoViewInput(fields["f358"], basis)
    assert len({view.NameValue for view in ordered.values()}) == len(ordered)
    distance, angle = owners.DriversValue
    linear, arc = (row.DisplayNode.FieldsValue for row in (distance, angle))
    ids = [
        fields["f2b0"][0]["v"] for fields in (linear, arc)
        if fields["n2b0"] == len(fields["f2b0"]) == 1
    ]
    assert len(ids) == 2 and ids[0] == ids[1]
    view = ordered[ids[0]]
    assert all(frame(row.DimensionNode.FieldsValue["ff0"])[0] == view.BasisValue
               and owners.FeatureValue.FieldsValue[slot] is row.DisplayNode
               and row.HandleNode.FieldsValue["ff0"] is row.DimensionNode
               and row.DimensionNode.FieldsValue["f28"] is row.ParameterNode
               for slot, row in zip(("f810", "f818"), (distance, angle), strict=True))
    flags = tuple(bool(fields["fb60"] & 0x100) for fields in (linear, arc))
    assert flags[0] == flags[1]
    linear_vector = ChmfViewPoint(distance.DisplayNode, "f880")
    assert linear_vector in ((0.0, 1.0, 0.0), (0.0, -1.0, 0.0))
    angles = points(angle.DimensionNode, ("f80", "fa0", "fc0"))
    first, second, centre = (angles[key] for key in ("f80", "fa0", "fc0"))
    radius = dist(centre, first)
    assert isclose(radius, dist(centre, second), rel_tol=0.0, abs_tol=1e-12)
    direction = ChmfViewPoint(angle.DisplayNode, "f880")
    intersection = ChmfViewPoint(angle.DisplayNode, "f9b8")
    text = tuple(anchor + value * arc["f8b0"] for anchor, value in zip(intersection, direction, strict=True))
    assert text[2] == 0.0
    return ChmfViewInput(
        tuple(ordered.values()), view.NameValue, (linear["f8a8"], linear_vector[1] * linear["f8b0"]),
        text[:2], radius, flags[0], (linear["ff80"], arc["ff80"]),
    )


def display_rows(owners):
    rows = []
    for index, driver in enumerate(owners.DriversValue):
        is_angle = index == 1
        display, dimension = driver.DisplayNode, driver.DimensionNode
        fields = display.FieldsValue
        values = ("f80", "fa0", "fc0") if is_angle else ("f80", "fa0", "fe0", "fe8")
        local = ("f880", "f958", "f970", "f988", "f9a0", "f9b8")
        tail = ("f100c", "f1010", "f1008", "f1018") if is_angle else ()
        scalars = ("f8b0", "fad0", "ffe8", "fff0", "fff8", "f1000") if is_angle else ("f8b0", "fad0")
        basis, translation = frame(dimension.FieldsValue["ff0"])
        rows.append({
            "driver": driver.NameValue, "value_si": driver.ValueSi,
            "feature": NativeNodeId(owners.FeatureValue), "driver_id": dimension.FieldsValue["f50"],
            "view_id": fields["f2b0"][0]["v"], "text_type": fields["f6a0"]["f10"],
            "leader": fields["ff80"], "design_intent": bool(fields["fb60"] & 0x100),
            "basis": basis, "station": fields["f8a8"], "arc": {key: fields[key] for key in tail},
            "vectors": {
                **{f"world:{key}": value for key, value in points(dimension, values).items()},
                **points(display, (*local, *(("ffb8", "ffd0") if is_angle else ("fa38",)))),
                "inverse_translation": translation,
            },
            "scalars": {key: fields[key] for key in scalars},
            "unclassified_f8a4": fields["f8a4"],
        })
    return rows


def exterior_scores(arc):
    first, second, direction = (arc["vectors"][key] for key in ("ffb8", "ffd0", "f880"))
    def cross_z(left, right):
        return left[0] * right[1] - left[1] * right[0]
    order = cross_z(first, second)
    scores = tuple(cross_z(ray, direction) * order for ray in (first, second))
    assert order > 1e-8 and (
        arc["station"] == -0.5 and scores[0] < -1e-8
        or arc["station"] == 1.5 and min(scores) > 1e-8
    )
    return scores


def compare_displays(source, built):
    errors = {}
    for reference, candidate in zip(source, built, strict=True):
        name = reference["driver"]
        compared = {"vectors", "scalars", "unclassified_f8a4", "feature", "driver_id"}
        assert {key: value for key, value in reference.items() if key not in compared} == {
            key: value for key, value in candidate.items() if key not in compared
        }, (reference, candidate)
        assert reference["feature"] - reference["driver_id"] == candidate["feature"] - candidate["driver_id"]
        vectors = {key: dist(value, candidate["vectors"][key]) for key, value in reference["vectors"].items()}
        scalars = {key: abs(value - candidate["scalars"][key]) for key, value in reference["scalars"].items()}
        assert max((*vectors.values(), *scalars.values())) <= 1e-12, (vectors, scalars)
        errors[name] = {"vector_and_scalar_checks": len(vectors) + len(scalars),
                        "max_difference": max((*vectors.values(), *scalars.values())),
                        "source_ids": [reference["feature"], reference["driver_id"]],
                        "generated_ids": [candidate["feature"], candidate["driver_id"]],
                        "generated_flags_outside_projection": candidate["unclassified_f8a4"]}
    exterior_scores(built[1])
    return errors
