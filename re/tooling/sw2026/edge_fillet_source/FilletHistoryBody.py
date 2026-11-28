from math import isclose

from FilletArchiveKernel import kernel_ownership
from FilletModel import predict, require
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import ReadBodyAttrs
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyScalar import ReadBodyScalar
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyTree import ReadBodyTree
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadImplicitName import ReadImplicit
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadCacheFaces import ReadCacheFaces

FACE_OWNERS = {40: ("moEndFaceSurfIdRep_c", 6, 4), 74: ("moFromSktEntSurfIdRep_c", 5, 4)}


def body_tracking(nodes, body):
    attributes = ReadBodyAttrs(nodes, body)
    values = {name: ReadBodyScalar(nodes, attributes, name, index)
              for name, index in (("ATOM_ID_2001", 1), ("LAST_BODY_MODIFYING_FEATURE_ID", 1), ("BODY_MATCH", 0))}
    label = attributes["SWIMPLICITBODYNAME_ID_U"]
    return values | {"label": ReadImplicit(nodes, attributes), "label_attribute": label.IndexValue,
                     "label_value_slot": label.Indexes("fields")[0], "body_slot": body.IndexValue}


def point_match(actual, expected):
    return all(isclose(a, b, rel_tol=0.0, abs_tol=1e-11) for a, b in zip(actual, expected, strict=True))


def point_set_match(actual, expected):
    return len(actual) == len(expected) and all(
        any(point_match(point, wanted) for point in actual) for wanted in expected)


def vertex_point(nodes, index):
    vertex = RequireXmt(nodes, index, 18)
    return RequireXmt(nodes, vertex.Integer("point"), 29).FieldsValue["pvec"]


def edge_incidence(nodes, index):
    edge = RequireXmt(nodes, index, 16)
    first = RequireXmt(nodes, edge.Integer("halfedge"), 17)
    other = RequireXmt(nodes, first.Integer("other"), 17)
    require(first.Integer("edge") == other.Integer("edge") == index and other.Integer("other") == first.IndexValue,
            "selected prior edge has an inconsistent fin pair")
    vertices = tuple(vertex_point(nodes, fin.Integer("vertex")) for fin in (first, other))
    faces = tuple(RequireXmt(nodes, fin.Integer("loop"), 15).Integer("face") for fin in (first, other))
    return vertices, faces


def stock_face_key(nodes, face, stock_id, epoch):
    attribute = ReadBodyAttrs(nodes, face)["FACE_ID_2001"]
    definition = RequireXmt(nodes, attribute.Integer("definition"), 80)
    fields = attribute.Indexes("fields")
    require(definition.Indexes("fields") == (9, 9, 1, 1) and len(fields) == 4 and fields[:2] == (0, 0),
            "prior stock face has an unqualified native identity definition")
    value = RequireXmt(nodes, fields[2], 82).Indexes("values")
    require(value and value[0] in FACE_OWNERS, "prior stock face has an alternate producer identity")
    cls, width, ordinal_index = FACE_OWNERS[value[0]]
    require(len(value) == width and value[1:3] == (stock_id, epoch),
            "prior stock face identity disagrees with its typed creating event")
    return cls, stock_id, epoch, value[ordinal_index]


def face_endpoint_hits(nodes, face, endpoints):
    carrier = RequireXmt(nodes, face.Integer("surface"), 50)
    normal, origin = (carrier.FieldsValue[key] for key in ("normal", "pvec"))
    return [index for index, point in enumerate(endpoints)
            if isclose(sum((x - y) * n for x, y, n in zip(point, origin, normal, strict=True)),
                       0.0, rel_tol=0.0, abs_tol=1e-11)]


def selected_support(nodes, tree, endpoints, stock_id, epoch, references):
    keys = {}
    for index in tree.FaceIds:
        face = RequireXmt(nodes, index, 14)
        key = stock_face_key(nodes, face, stock_id, epoch)
        require(key not in keys, "prior stock face identities are ambiguous")
        keys[key] = face
    (edge,) = (index for index in tree.EdgeIds if point_set_match(edge_incidence(nodes, index)[0], endpoints))
    _, adjacent = edge_incidence(nodes, edge)
    rows = []
    for reference in references:
        face = keys[(reference["owner"]["class"], reference["feature_id"], reference["creation_word"], reference["f38"])]
        rows.append({"face_slot": face.IndexValue, "surface_slot": face.Integer("surface"),
                     "representation_class": reference["owner"]["class"], "ordinal": reference["f38"],
                     "incident_to_edge": face.IndexValue in adjacent, "endpoints_on_face": face_endpoint_hits(nodes, face, endpoints)})
    require(len({row["face_slot"] for row in rows}) == 4 == len(rows)
            and {row["face_slot"] for row in rows[:2]} == set(adjacent)
            and all(row["endpoints_on_face"] == [0, 1] for row in rows[:2])
            and sorted(row["endpoints_on_face"] for row in rows[2:]) == [[0], [1]]
            and not any(row["incident_to_edge"] for row in rows[2:]),
            "stored support sequence does not bind the two incident faces and the two endpoint planes")
    return {"edge_slot": edge, "faces_in_archive_order": rows}


def check_shape_state(active, previous, expected, case, atom, owners):
    observed = expected["native_reopen"]
    kernel = kernel_ownership(active, atom, observed)
    active_body = RequireXmt(active, kernel["body_node"], 12)
    active_faces = ReadCacheFaces(active, active_body)
    require(len(active_faces) == observed["body_counts"]["faces"], "selected shell does not own all fillet faces")
    current = body_tracking(active, active_body)
    tree = ReadBodyTree(previous)
    preceding = body_tracking(previous, RequireXmt(previous, tree.BodyIndex, 12))
    require(current["body_slot"] == preceding["body_slot"]
            and current["LAST_BODY_MODIFYING_FEATURE_ID"] == owners["fillet"]["native_id"]
            and preceding["LAST_BODY_MODIFYING_FEATURE_ID"] == owners["stock"]["native_id"]
            and current["ATOM_ID_2001"] == preceding["ATOM_ID_2001"] == atom["f140"]
            and current["BODY_MATCH"] == preceding["BODY_MATCH"] == atom["f180"]
            and current["label"] == owners["fillet"]["name"] and preceding["label"] == owners["stock"]["name"],
            "historical body identity changes beyond the measured fillet ownership")
    independent = predict(case)
    vertices = tuple(vertex_point(previous, index) for index in tree.VertexIds)
    require(point_set_match(vertices, independent["vertices"]), "recovered stock vertices disagree with independent stock")
    selected = owners["edge_owners"]["f848_selected_edge"]["surfaces"]
    support = selected_support(previous, tree, observed["edge_endpoints_m"], preceding["LAST_BODY_MODIFYING_FEATURE_ID"],
                               selected[0]["creation_word"], selected)
    return {"selected": current, "prior_stock": preceding, "previous_stock_counts": independent["counts"],
            "stock_selected_support": support}
