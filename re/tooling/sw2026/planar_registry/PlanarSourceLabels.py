from hashlib import sha256

from PlanarPriorAdmission import source_intent
from RectanglePresentation import point, require

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import ReadPrincAxis
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineParamId import LineParamId
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadLineDims import ReadLineDims
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


def one(values, description):
    matches = tuple(values)
    require(len(matches) == 1, "expected one actual " + description)
    return matches[0]


def check_relation(source_sketch, profile, profile_step, source_child, driver):
    slot = driver.IndexValue
    native_id = profile.FieldsValue["f08"]
    dimension_id = driver.NodeValue.FieldsValue["f50"]
    parameter_id = LineParamId(native_id, driver.NameValue)
    require(source_sketch.parameter_ids[slot] == parameter_id,
            "native dimension parameter does not own the selected source sketch slot")
    relation = one((row for row in source_sketch.constraints if row.parameter_id == parameter_id),
                   "source sketch relation for the selected parameter")
    require(relation.kind == "distance" and relation.driving and not relation.suppressed
            and [(row.entity_id, row.point) for row in relation.references]
            == [(source_sketch.entities[slot].id, key) for key in ("start", "end")],
            "native rectangle label selects another source relation or edge")
    require(dict(relation.attributes) == {
        "native_code": 1, "native_dimension_id": dimension_id, "native_point_indices": driver.PointValues,
        "native_display_index": driver.DisplayValue.IndexValue, "native_handle_index": driver.HandleValue.IndexValue,
        "native_parameter_owner": driver.ParamOwner, "typed_archive_owner": driver.OwnerValue,
    }, "native rectangle display does not match the strict source relation owner")
    parameter = one((row for row in source_child.parameters if row.id == parameter_id),
                    "source parameter for the selected relation")
    require(parameter.owner_id == profile_step.id and str(parameter.role) == "driving"
            and parameter.value.unit == "mm" and parameter.attributes["native_value"] == driver.MetresValue
            and parameter.attributes["typed_archive_owner"] == {
                **driver.ParamOwner, "value_field": "f58", "dimension_id": dimension_id,
                "dimension_index": driver.NodeValue.IndexValue, "display_index": driver.DisplayValue.IndexValue,
                "handle_index": driver.HandleValue.IndexValue, "group_index": slot,
            }, "native rectangle label does not match the strict source parameter owner")
    return relation, parameter


def project_labels(source_child, child_bytes, target_child, measured):
    require(sha256(child_bytes).hexdigest() == source_child.source.sha256,
            "label observations require the exact physically resolved source child")
    source_sketch, = source_child.sketches
    target_sketch, = target_child.sketches
    support = one((plane for plane in source_child.support_planes if plane.id == source_sketch.support_plane_id),
                  "support plane of the selected source sketch")
    require(ReadPrincAxis(support.transform) == "z",
            "label observations require the canonical origin Front frame")
    link = ReadNativeLink(SldprtArchive.from_bytes(child_bytes), 0)
    profile = one((node for node in link.ResolvedValue.RootsValue if isinstance(node, ArchiveNode)
                   and node.ClassValue.NameValue == "moProfileFeature_c"
                   and node.FieldsValue.get("f08") == source_sketch.attributes["native_object_id"]
                   and ReadNodeName(node) == source_sketch.name), "typed source profile")
    sketch_node = RequireNative(profile.FieldsValue["pd_f80"], "sgSketch")
    profile_step = one((row for row in source_child.feature_timeline if row.sketch_id == source_sketch.id
                        and row.name == source_sketch.name
                        and getattr(row.definition, "object_data", {}).get("native_class") == "moProfileFeature_c"),
                       "source profile feature for the selected sketch")
    require(source_sketch.attributes["typed_archive_owner"] == NativeNodeSpan(link, sketch_node)
            and profile_step.attributes["typed_archive_owner"] == NativeNodeSpan(link, profile),
            "native profile or sketch archive identity differs from the strict source owners")
    rows = ReadLineDims(sketch_node, link).DriverValues
    require(tuple(row.NameValue for row in rows) == ("D1", "D2"),
            "label observations require two ordinary rectangle driving roles")
    labels, origins = [], {}
    for axis, row in zip(("width", "height"), rows, strict=True):
        relation, source_param = check_relation(source_sketch, profile, profile_step, source_child, row)
        parameter_id = target_sketch.parameter_ids[row.IndexValue]
        target_param = one((value for value in target_child.parameters if value.id == parameter_id),
                           "projected driver for the selected label")
        require(target_param.name == source_param.name and target_param.owner_id == target_sketch.id
                and target_param.value == source_param.value,
                "projected child label does not target the corresponding driving value")
        fields = row.DisplayValue.FieldsValue
        route = fields["f1014"]
        require(type(route) is int and route in (0, 0x800) and fields["f6a0"]["f10"] == 18,
                "native rectangle label has unsupported routing or text-owner state")
        xyz = point(fields["f6a0"]["f38"])
        require(xyz == measured[axis]["text_m"] and bool(route) is measured[axis]["centerline_route"],
                "source label placement differs from independent disclosure")
        labels.append({"sketch_id": target_sketch.id, "parameter_id": parameter_id,
                       "text_point_m": xyz, "route_centerline": bool(route)})
        origins[row.NameValue] = {
            "source_parameter_id": source_param.id, "source_relation_id": relation.id,
            "source_profile_id": profile.FieldsValue["f08"], "source_sketch_map_index": sketch_node.IndexValue,
            "source_value_id": row.NodeValue.FieldsValue["f50"], "source_value_index": row.NodeValue.IndexValue,
            "source_display_id": fields["f58"], "source_display_index": row.DisplayValue.IndexValue,
            "source_handle_index": row.HandleValue.IndexValue, "source_route_word": route,
            "source_value_slot": row.IndexValue,
        }
    return labels, origins


def bridge(source_document, authored_case, child_bytes, measured):
    document, source = source_intent(source_document, authored_case, child_bytes)
    require(source["source_display"] == measured,
            "strict decoded rectangle differs from the independently frozen prior observation")
    source_child = source_document.assembly.documents[0].document
    projected_child = document.assembly.documents[0].document
    labels, origins = project_labels(source_child, child_bytes, projected_child, measured)
    return document, labels, origins
