from math import isclose, radians

from AuditPrincipalReader import FRAMES, point, to_xyz
from AuditRevEndOwners import observe_ends
from BuildSquareRevolves import project
from ProveTwoDirectionRevolves import need
from SquareEdgeRoles import contour_roles, edge_role
from convert import open_document
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import ReadRevOwners
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureAngleRev import AngularRevolve


def close(first, second, *, tolerance=1e-13):
    return isclose(first, second, rel_tol=tolerance, abs_tol=1e-12)


def contour_relations(sketch, case, archive_equal):
    roles = contour_roles(case)
    contour = {entity.id: edge_role(roles, [(point.x * .001, point.y * .001) for point in (
        entity.geometry.start, entity.geometry.end)]) for entity in sketch.entities if not entity.construction}
    equal, = [rule for rule in sketch.constraints if rule.kind == "equal"]
    unary = [rule for rule in sketch.constraints if rule is not equal]
    need(len(contour) == 4 and set(contour.values()) == set(range(4)) and len(unary) == 4 and all(
        len(rule.references) == 1 and rule.driving and not rule.suppressed and rule.references[0].entity_id in contour
        and not rule.references[0].point for rule in unary), "four ordinary unary contour owners")
    need(sorted((contour[rule.references[0].entity_id], rule.kind) for rule in unary)
         == [(0, "horizontal"), (1, "vertical"), (2, "horizontal"), (3, "vertical")], "complete unary owner order")
    need(equal.driving and not equal.suppressed and equal.parameter_id is None and equal.provenance is not None
         and all(ref.entity_id in contour and not ref.point for ref in equal.references)
         and [contour[ref.entity_id] for ref in equal.references] == case["equal_edges"]
         and equal.attributes["native_code"] == 14
         and equal.attributes["native_line_indices"] == archive_equal.Indices
         and equal.attributes["typed_archive_owner"] == archive_equal.OwnerValue,
         "explicit equal relation preserved through the exact solver handles")


def verify_document(doc, case, owner, wire, observed, *, cached, history):
    doc.assert_valid()
    (feature,) = [row for row in doc.feature_timeline if type(row.definition) is AngularRevolve]
    (body,) = doc.bodies
    selected, = doc.configurations
    need(feature.id == body.final_feature_id and selected.active and selected.name == observed["profile"]["configuration"],
         "actual configuration and final body creator")
    definition = feature.definition
    actual = owner.EndValue
    along, against = definition.AlongParameterId, definition.AgainstParameterId
    drivers = (along,) if against is None else (along, against)
    expected = (radians(case["angle_deg"]),)
    if case["mode"] == "two":
        expected += (radians(case["second_deg"]),)
    need(len(drivers) == len(expected) and len(set(drivers)) == len(drivers) and feature.parameter_ids == drivers
         and definition.SideMode == actual.ModeValue, "ordinary active angle driver inventory")
    params = {param.id: param for param in doc.parameters}
    need(set(params) == set(drivers), "exact editable parameter inventory")
    for index, (identity, key, target) in enumerate(zip(drivers, ("f18", "f20")[:len(drivers)], expected, strict=True)):
        param, typed = params[identity], wire["angles"][key]
        need(param.name == typed["name"] == f"D{index + 1}" and param.owner_id == feature.id
             and param.role is ParameterRole.KDriving and param.value.kind is ValueKind.KAngle and param.value.unit == "rad"
             and param.value.value == typed["radians"] and close(param.value.value, target)
             and close(param.value.value, observed["angles_radians"][index])
             and param.attributes["native_dimension_id"] == typed["dimension_id"]
             and param.attributes["typed_archive_owner"] == typed["owners"][3] | {
                 "slot": "f8d8." + key, "value_field": "f58"}, "actual independent angular parameter owner")
    interval = (-expected[0] / 2, expected[0] / 2) if len(expected) == 1 else (-expected[1], expected[0])
    need(all(close(a, b) for a, b in zip(actual.IntervalValue, interval, strict=True))
         and (actual.AgainstValue is not None) == (len(expected) == 2), "total symmetric or independently bounded sweep")
    sketch, = [item for item in doc.sketches if item.id == feature.sketch_id]
    axis, = [item for item in sketch.entities if item.construction]
    selection, = [item for item in doc.selections if item.id == definition.AxisSelectionId]
    support, = [item for item in doc.support_planes if item.id == sketch.support_plane_id]
    frame = FRAMES[case["plane"]]
    origin = point(case["plane"], case["axis_x_m"] * 1000, case["axis_axial_m"][0] * 1000)
    direction = tuple((-1 if case["reverse"] else 1) * offset for offset in frame[1])
    need(tuple(item.entity_id for item in selection.path) == (sketch.id, axis.id)
         and to_xyz(support.transform.origin) == (0, 0, 0)
         and tuple(to_xyz(value) for value in (support.transform.x_axis, support.transform.y_axis, support.transform.z_axis)) == frame
         and all(close(a, b) for a, b in zip(to_xyz(definition.AxisOrigin), origin, strict=True))
         and to_xyz(definition.AxisDirection) == direction and owner.IsReverse == case["reverse"],
         "actual selected local axis and canonical support")
    contour_relations(sketch, case, owner.ProfileGraph.EqualValue)
    if history:
        need(doc.brep is None and not doc.brep_payloads, "history-only read does not materialize cache")
    else:
        brep = doc.brep
        need([body.name] == observed["body_names"] and brep is not None and len(brep.bodies) == 1
             and not brep.validate(frozenset((body.id,)))
             and (len(brep.faces), len(brep.edges), len(brep.vertices)) == (6, 12, 8)
             and tuple(item.kind for item in doc.brep_payloads) == (("partition", "deltas") if cached else ()),
             "strict native saved or reconstructed partial solid")
        if not cached:
            need(close(body.topology.volume, observed["mass"]["volume"] * 1e9, tolerance=2e-7)
                 and close(body.topology.surface_area, observed["mass"]["area"] * 1e6, tolerance=2e-7),
                 "cold analytic shape agrees with native dimensions")
    return len(drivers)


def strict_square(raw, case, observed, cached):
    pair, linked = project(raw, case)
    need(list(pair) == case["equal_edges"] and linked["line_reference_counts"] == [2, 2]
         and len(linked["streams"]) == 2, "ordinary typed square archive and ordered owners")
    link = ReadNativeLink(SldprtArchive.from_bytes(raw), 0)
    owner, = ReadRevOwners(link)
    wire = observe_ends(link, owner.NodeValue)
    scope = {"midplane": "symmetric_full", "two": "two_sided"}
    need(owner.EndValue.ModeValue == scope[case["mode"]], "actual native end mode")
    counts = set()
    for history in (False, True):
        options = {"include_brep": False, "include_tessellation": False} if history else {}
        doc = open_document(raw, source_format="solidworks.sldprt", strict=True, **options)
        counts.add(verify_document(doc, case, owner, wire, observed, cached=cached, history=history))
    drivers, = counts
    return {"strict_reads": 2, "relation_count": 5, "driver_count": drivers, "linked_streams": 2,
            "body_topology": [6, 12, 8], "cached": cached}
