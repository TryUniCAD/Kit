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
