from math import isclose, radians

from AuditPrincipalReader import FRAMES, point, to_xyz
from AuditRevEndOwners import audit_streams, observe_ends

from convert import open_document
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import ReadRevOwners
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureAngleRev import AngularRevolve


class ParityFailure(ValueError):
    pass


def need(value, check):
    if not value:
        raise ParityFailure(check)


def close(first, second):
    return isclose(first, second, rel_tol=1e-13, abs_tol=1e-14)


def point_equal(first, second):
    return all(close(a, b) for a, b in zip(first, second, strict=True))


def angles(case):
    return [radians(case["angle_deg"]), radians(case["second_deg"])]


def strict_history(raw, case, observed, *, cached):
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    (owner,) = ReadRevOwners(link)
    end = owner.EndValue
    need(end.ModeValue == "two_sided" and end.AgainstValue is not None, "typed end mode")
    wire = observe_ends(link, owner.NodeValue)
    need(tuple(wire["end_words"][key] for key in ("f08", "f0c", "f10")) == (0, 0, 0)
         and wire["feature_words"]["f820"] == 0, "modern blind end words")
    need(wire["feature_words"]["f824"] == int(case["reverse"]) and owner.IsReverse == case["reverse"], "reverse ownership")
    actual = [end.AlongValue.RadiansValue, end.AgainstValue.RadiansValue]
    need(point_equal(actual, angles(case)) and point_equal(actual, observed["angles_radians"]), "both actual radian owners")
    need(end.IntervalValue == (-actual[1], actual[0]), "signed sweep interval")
    streams = audit_streams(archive, link)
    need(len(streams) == 2, "exact linked native streams")
    expected_axis = [point(case["plane"], case["axis_x_m"] * 1000.0, axial * 1000.0)
                     for axial in case["axis_axial_m"]]
    need(point_equal(to_xyz(owner.FrameValue.StartValue), expected_axis[0]) and
         point_equal(to_xyz(owner.FrameValue.EndValue), expected_axis[1]), "actual ordered axis endpoints")
    sense = -1.0 if case["reverse"] else 1.0
    expected_direction = tuple(sense * value for value in FRAMES[case["plane"]][1])
    need(to_xyz(owner.FrameValue.DirectionValue) == expected_direction, "effective principal axis")
    results = {}
    for mode, opts in (("default", {}), ("history", {"include_brep": False, "include_tessellation": False})):
        doc = open_document(raw, source_format="solidworks.sldprt", strict=True, **opts)
        doc.assert_valid()
        features = [feature for feature in doc.feature_timeline if type(feature.definition) is AngularRevolve]
        need(len(features) == 1 and len(doc.bodies) == len(doc.configurations) == 1, "strict one-body history")
        if "profile" in observed:
            need(doc.configurations[0].name == observed["profile"]["configuration"], "saved active configuration")
        feature = features[0]
        definition = feature.definition
        need(definition.SideMode == "two_sided" and definition.AgainstParameterId is not None, "projected independent limits")
        keys = definition.AlongParameterId, definition.AgainstParameterId
        need(keys == feature.parameter_ids and len(set(keys)) == 2, "ordered distinct native drivers")
        params = {row.id: row for row in doc.parameters if row.owner_id == feature.id}
        need(set(params) == set(keys), "exact feature-owned parameter inventory")
        for index, (key, slot) in enumerate(zip(keys, ("f18", "f20"), strict=True)):
            param = params[key]
            watched = wire["angles"][slot]
            anchor = param.attributes["typed_archive_owner"]
            need(param.name == ("D1", "D2")[index] and param.value.value == actual[index]
                 and param.value.unit == "rad" and param.value.kind is ValueKind.KAngle
                 and param.role is ParameterRole.KDriving, "owned live projected driver")
            need(anchor == watched["owners"][3] | {"slot": "f8d8." + slot, "value_field": "f58"}
                 and param.attributes["native_dimension_id"] == watched["dimension_id"], "real dimension and parameter slot")
        need(point_equal(to_xyz(definition.AxisOrigin), expected_axis[0]) and
             to_xyz(definition.AxisDirection) == expected_direction, "public selected frame")
        (sketch,) = (item for item in doc.sketches if item.id == feature.sketch_id)
        (axis,) = (item for item in sketch.entities if item.construction)
        (selection,) = (item for item in doc.selections if item.id == definition.AxisSelectionId)
        need(len(sketch.entities) == 5 and len(sketch.constraints) == 4 and
             tuple(item.entity_id for item in selection.path) == (sketch.id, axis.id), "actual sketch and selected line")
        need(feature.id == doc.bodies[0].final_feature_id, "actual final body creator")
        if mode == "default":
            need(doc.brep is not None and len(doc.brep.bodies) == 1 and not doc.brep.validate(
                frozenset((doc.bodies[0].id,))), "strict standalone B-rep")
            need((len(doc.brep.faces), len(doc.brep.edges), len(doc.brep.vertices)) == (6, 12, 8), "partial revolve topology")
            need(tuple(item.kind for item in doc.brep_payloads) == (("partition", "deltas") if cached else ()), "saved versus cold geometry")
            need([doc.bodies[0].name] == observed["body_names"], "actual native body name")
            if not cached:
                need(isclose(doc.bodies[0].topology.volume, observed["mass"]["volume"] * 1e9, rel_tol=2e-7)
                     and isclose(doc.bodies[0].topology.surface_area, observed["mass"]["area"] * 1e6, rel_tol=2e-7), "cold analytic/native measures")
        else:
            need(doc.brep is None and not doc.brep_payloads, "history-only projection")
        results[mode] = True
    return {"exact_linked_streams": len(streams), "strict_reads": len(results), "driver_count": 2,
            "partial_brep_topology": [6, 12, 8], "cached": cached}
