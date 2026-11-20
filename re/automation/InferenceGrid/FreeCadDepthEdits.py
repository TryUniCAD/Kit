# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from collections import defaultdict
from dataclasses import replace
import hashlib

from convert.adapters.freecad.Archive import ExtractManifest
from convert.adapters.freecad.EditRead.EditObjects import RequireEditObj
from convert.adapters.freecad.EditRead.EditExtrusion import ReadShapeEntry
from convert.adapters.freecad.EditRead.XmlField import EditChild, EditFloat, EditScalar
from convert.adapters.freecad.InlineRead.ReadInline import ReadExpected, ReadInlineDepth, ReadInlineExpr
from convert.adapters.freecad.ExtrusionCache.InlineProfile import ReadCacheFrame
from convert.adapters.freecad.ExtrusionCache.InlineShape import CacheStations
from convert.adapters.freecad.EditShape.PrismShape import IsEditPrism
from convert.Geometry.Extrude.Polygon.PrismRing import ReadPrismRing
from interchange.geometry.Models.VectorSpace import SpaceVector
from convert.adapters.freecad.Native import LoadNative, ReadNativeFcstd


def saved_prism(archive, manifest, key, obj, before):
    profile = ReadCacheFrame(manifest, key)
    if not profile or not isinstance(profile[1], tuple):
        return {"status": "unsupported_profile"}
    frame, lines = profile
    vector = EditChild(obj, "Dir", "App::PropertyVector", "PropertyVector")
    direction = tuple(EditFloat(vector, "value" + axis) for axis in "XYZ")
    flags = [EditScalar(obj, field, "App::PropertyBool", "Bool") for field in ("Symmetric", "Reversed")]
    if any(value not in ("true", "false") for value in flags):
        return {"status": "unsupported_flags"}
    member = ReadShapeEntry(obj)
    shape = archive.entries.get(member)
    if not shape:
        return {"status": "missing_shape"}
    ring = ReadPrismRing(lines)
    result = {"member": member, "sha256": hashlib.sha256(shape).hexdigest()}
    for label, source in (("saved", obj), ("embedded", before)):
        stations = CacheStations(direction, frame.z_axis, ReadInlineDepth(source, "LengthFwd"),
                                 ReadInlineDepth(source, "LengthRev"), *(value == "true" for value in flags))
        if stations is None:
            return {**result, "status": "unsupported_direction"}
        lower, upper = stations
        origin = SpaceVector(*(getattr(frame.origin, c) + lower * getattr(frame.z_axis, c) for c in "xyz"))
        result[label + "_stations_mm"] = stations
        result[label + "_depths_match"] = IsEditPrism(shape, replace(frame, origin=origin), ring, upper - lower)
    result["status"] = ("edited_prism_confirmed" if result["saved_depths_match"] and not result["embedded_depths_match"]
                        else "prism_unverified")
    return result


def depth_edits(data):
    archive = LoadNative(data)
    objects = archive.objects
    manifest = ExtractManifest(data)
    expected = ReadExpected(manifest)
    native = ReadNativeFcstd(data)
    parameters = defaultdict(list)
    for parameter in native.parameters:
        parameters[parameter.id].append(parameter)
    changes = []
    for obj in objects:
        if obj.type_id != "Part::Extrusion":
            continue
        key = EditScalar(obj, "KitId", "App::PropertyString", "String")
        before = RequireEditObj(expected, key, "Part::Extrusion")
        RequireEditObj(objects, key, "Part::Extrusion")
        expressions = ReadInlineExpr(obj)
        geometry = None
        for field in ("LengthFwd", "LengthRev"):
            old, new = ReadInlineDepth(before, field), ReadInlineDepth(obj, field)
            if old == new:
                continue
            row = {"kit_feature_id": key, "native_object": obj.name, "field": field,
                   "embedded_mm": old, "saved_mm": new, "status": "native_property_only"}
            current = parameters[f"freecad:parameter:{obj.name}:{field}"]
            if len(current) == 1:
                prop = current[0]
                expr = prop.expression
                if (prop.owner_id == "freecad:feature:" + obj.name and prop.value.unit == "mm"
                        and prop.value.value == new and expr and expr.source == expressions.get(field)
                        and len(expr.parameter_ids) == 1):
                    cells = parameters[expr.parameter_ids[0]]
                    if len(cells) == 1:
                        cell = cells[0]
                        row.update(expression=expr.source, driver_id=cell.id, driver_unit=cell.value.unit,
                                   driver_value=cell.value.value, status="resolved_native_dependency")
            if geometry is None:
                try:
                    geometry = saved_prism(archive, manifest, key, obj, before)
                except ValueError as error:
                    geometry = {"status": "prism_unverified", "reason": str(error)[:256]}
            row["saved_geometry"] = geometry
            changes.append(row)
    return changes


def reconcile_depths(data, changes, bindings=None):
    import json
    from convert.adapters.freecad.InlineRead.CheckInline import GuardInline
    from convert.adapters.freecad.InlineRead.ReadInline import ReadInlineScope
    from interchange.document.Models.DocumentModel import CadDocument

    if not changes or any(row.get("status") != "resolved_native_dependency"
                          or row.get("saved_geometry", {}).get("status") != "edited_prism_confirmed"
                          for row in changes):
        return {"status": "insufficient_edit_evidence"}
    archive = LoadNative(data, LoadEntries=False)
    graph = ExtractManifest(data)
    expected = ReadExpected(graph)
    metadata, = (obj for obj in expected if obj.name == "KitMetadata")
    sheet, = (obj for obj in expected if obj.type_id == "Spreadsheet::Sheet")
    aliases = json.loads(EditScalar(metadata, "ParameterAliasesJSON", "App::PropertyString", "String"))
    updates = []
    for row in changes:
        key, field = row["kit_feature_id"], row["field"]
        original = RequireEditObj(expected, key, "Part::Extrusion")
        expression = row["expression"]
        if ReadInlineExpr(original).get(field) != expression:
            raise ValueError("saved expression differs from original end binding")
        ident, = (ident for ident, alias in aliases.items() if sheet.name + "." + alias == expression)
        step, = (step for step in graph["feature_timeline"]["$tuple"] if step["id"] == key)
        parameter, = (p for p in graph["parameters"]["$tuple"] if p["id"] == ident)
        if (parameter["owner_id"] != key or step["parameter_ids"]["$tuple"].count(ident) != 1
                or parameter.get("expression") or parameter["role"]["value"] != "driving"):
            raise ValueError("embedded driving parameter ownership differs")
        if parameter["value"].get("value") != row["embedded_mm"]:
            raise ValueError("original parameter value differs")
        baseline = RequireEditObj(ReadExpected(graph), key, "Part::Extrusion")
        candidates = []
        for slot, value in step["definition"].items():
            if bindings is not None and bindings.get(field) != slot:
                continue
            if (not isinstance(value, dict) or value.get("$type") != "ParameterValue"
                    or value.get("kind", {}).get("value") != "length" or value.get("unit") != "mm"
                    or value.get("value") != row["embedded_mm"]):
                continue
            parameter["value"]["value"] = value["value"] = row["saved_mm"]
            try:
                probe = RequireEditObj(ReadExpected(graph), key, "Part::Extrusion")
                if all(ReadInlineDepth(probe, name) == (row["saved_mm"] if name == field else ReadInlineDepth(baseline, name))
                       for name in ("LengthFwd", "LengthRev")):
                    candidates.append(slot)
            except ValueError:
                continue
            finally:
                parameter["value"]["value"] = value["value"] = row["embedded_mm"]
        if len(candidates) != 1:
            raise ValueError("controlled graph variations did not identify one native end")
        slot = candidates[0]
        for value in (parameter["value"], step["definition"][slot]):
            if not value or value["kind"]["value"] != "length" or value["unit"] != "mm" or value["value"] != row["embedded_mm"]:
                raise ValueError("embedded parameter or extrusion distance differs")
            value["value"] = row["saved_mm"]
        updates.append({"parameter_id": ident, "feature_id": key, "definition_field": slot,
                        "before_mm": row["embedded_mm"], "after_mm": row["saved_mm"]})
    document = CadDocument.from_dict(graph)
    document.assert_valid()
    if ReadInlineScope(document, graph) is None:
        raise ValueError("candidate falls outside inline graph verification")
    GuardInline(document, graph, archive.root, RetainedRoute=False)
    return {"source_sha256": hashlib.sha256(data).hexdigest(),
            "status": "candidate_matches_native_graph", "updates": updates, "candidate": graph}
