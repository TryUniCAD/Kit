# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from collections import defaultdict

from convert.adapters.freecad.Archive import ExtractManifest
from convert.adapters.freecad.EditRead.EditObjects import RequireEditObj
from convert.adapters.freecad.EditRead.XmlField import EditScalar
from convert.adapters.freecad.InlineRead.ReadInline import ReadExpected, ReadInlineDepth, ReadInlineExpr
from convert.adapters.freecad.Native import LoadNative, ReadNativeFcstd


def depth_edits(data):
    objects = LoadNative(data, LoadEntries=False).objects
    expected = ReadExpected(ExtractManifest(data))
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
            changes.append(row)
    return changes
