# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import math
import re
import sys
from pathlib import Path

from convert.adapters.Fusion.Native.FixedPrism.ReadFixedRect import ReadFixedRect
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, ResolveField
from convert.adapters.Fusion.Native.Graph.ReadExtentMode import ReadExtentMode
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Parameters.ParamExpression import ParamExpression
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.Formats.Fusion.DocumentCodec.CheckDocSpec import CheckDocSpec

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "SavedCuboidGeneration"))
from GenerateSemantic import exact_fields, label, number, request_spec, require

SCOPE = "fixed_cuboid_parameter_bindings"
AXES = ("width", "depth", "height")
MODELS = (*AXES, "taper")
DRIVERS = tuple(f"{axis}_driver" for axis in AXES)
ROLES = (*DRIVERS, *MODELS)
PARAMETER_FIELDS = ("user_name", "display_name", "unit", "expression", "value", "comment")
LITERAL = re.compile(
    r"\s*([+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)\s*(mm|deg)\s*", re.ASCII
)
OPEN_SCOPE = [
    "saved_camera_views",
    "saved_graphics_and_selection",
    "saved_visibility_and_previews",
    "saved_configuration_parts",
    "saved_appearance_and_material_graph",
    "saved_procedural_mapping",
]


def optional_text(value, path):
    if value == "":
        require(type(value) is str, f"{path} requires text")
        return value
    return label(value, path)


def literal_length(row, unit, role):
    match = LITERAL.fullmatch(row["expression"])
    require(match is not None and match[2] == unit, f"{role} requires an explicit {unit} literal")
    amount = float(match[1])
    require(math.isfinite(amount), f"{role} literal is not finite")
    value = row["value"]
    if unit == "deg":
        require(amount == value == 0, "Only a zero taper is supported")
    else:
        require(
            amount > 0 and value > 0 and value in (amount * 0.1, amount / 10),
            f"{role} millimetre literal does not match stored centimetres",
        )
    return amount


def validate(request):
    keys = (
        "schema",
        "scope",
        "title",
        "component_title",
        "names",
        "material",
        "parameter_order",
        "parameters",
    )
    request = exact_fields(request, keys, "request")
    require(
        type(request["schema"]) is int and request["schema"] == 1 and request["scope"] == SCOPE,
        "Unsupported saved cuboid binding request",
    )
    optional_text(request["title"], "title")
    order = request["parameter_order"]
    require(
        type(order) is list
        and len(order) == len(ROLES)
        and all(type(role) is str for role in order)
        and set(order) == set(ROLES),
        "Parameter order requires each symbolic role exactly once",
    )
    parameters = exact_fields(request["parameters"], ROLES, "parameters")
    for role, row in parameters.items():
        fields = (*PARAMETER_FIELDS, "driver_role") if role in AXES else PARAMETER_FIELDS
        exact_fields(row, fields, role)
        for field in ("user_name", "display_name", "expression"):
            label(row[field], f"{role}.{field}")
        optional_text(row["comment"], f"{role}.comment")
        require(row["unit"] == ("deg" if role == "taper" else "mm"), f"Unexpected {role} unit")
        parameter_name = row["user_name"]
        require(parameter_name.isascii() and parameter_name.isidentifier(), f"Unsupported {role} identifier")
        number(row["value"], f"{role}.value")
    require(
        len({row["user_name"] for row in parameters.values()}) == len(ROLES),
        "Parameter names must be distinct",
    )
    sizes = {}
    drivers = {}
    for axis, role in zip(AXES, DRIVERS, strict=True):
        user, model = parameters[role], parameters[axis]
        require(
            model["driver_role"] == role
            and model["expression"] == user["user_name"]
            and model["value"] == user["value"],
            f"{axis} model must use the exact independent {role} name and value",
        )
        sizes[axis] = literal_length(user, "mm", role)
        drivers[axis] = user["user_name"]
    literal_length(parameters["taper"], "deg", "taper")
    spec = request_spec(
        {
            "schema": 1,
            "title": request["component_title"],
            "dimensions_mm": sizes,
            "drivers": drivers,
            "names": request["names"],
            "material": request["material"],
        }
    )
    CheckDocSpec(spec)
    return spec


def parameter_row(node):
    fields = node.Fields
    return {
        "user_name": fields["userName"],
        "display_name": fields["name"],
        "unit": fields["unit"],
        "expression": fields["expression"],
        "value": fields["value"],
        "comment": fields["comment"],
    }


def extract(model, public):
    graph = BuildGraph(model)
    context = SelectExtrusion(graph)
    require(
        len(model.Snapshots) == len(model.Bodies) == 1
        and isinstance(model.Bodies[0].History, PrismHistory)
        and model.Bodies[0].History.Model.BasePoint == (0.0, 0.0, 0.0)
        and ReadExtentMode(context.Extrude) == "one_sided",
        "Expected a saved fixed-corner positive XY cuboid",
    )
    rectangle = ReadFixedRect(graph, context)
    dimensions = {dimension.Fields["constraintType"]: dimension for dimension in rectangle.Dimensions}
    require(set(dimensions) == {1 << 22, 1 << 23}, "Expected two independent axis dimensions")
    slots = {
        "width": ResolveField(graph, dimensions[1 << 22], "dcParameter", "DcDoubleParameter"),
        "depth": ResolveField(graph, dimensions[1 << 23], "dcParameter", "DcDoubleParameter"),
        "height": context.Along,
        "taper": context.Taper,
    }
    table = ResolveField(graph, context.Component, "rParameterTable", "ParameterTable")
    nodes = LinkedNodes(graph, table, "children")
    catalog = {node.Fields["userName"]: node for node in nodes}
    by_id = {node.Identity: node for node in nodes}
    selected = {role: ResolveField(graph, slot, "parameter", "Parameter") for role, slot in slots.items()}
    parameters = {role: parameter_row(parameter) for role, parameter in selected.items()}
    for axis, driver_role in zip(AXES, DRIVERS, strict=True):
        (dependency,) = ParamExpression(selected[axis], catalog).parameter_ids
        selected[driver_role] = by_id[dependency]
        parameters[driver_role] = parameter_row(selected[driver_role])
        parameters[axis]["driver_role"] = driver_role
    role_by_id = {parameter.Identity: role for role, parameter in selected.items()}
    require(
        set(role_by_id) == set(by_id) and len(nodes) == len(ROLES),
        "Saved graph has unsupported parameter inventory",
    )
    (configuration,) = public.configurations
    sketch, extrude = public.feature_timeline
    names = {"sketch": public.sketches[0].name, "extrude": extrude.name, "body": public.bodies[0].name}
    require(
        configuration.active and sketch.name == names["sketch"],
        "Saved graph has different named sketch roles",
    )
    (material,) = public.materials
    require(public.bodies[0].material_id == material.id, "Saved cuboid lacks a unique linked body material")
    result = {
        "schema": 1,
        "scope": SCOPE,
        "title": configuration.name,
        "component_title": context.Component.Fields["userName"],
        "names": names,
        "material": {
            "label": material.name,
            "density_kg_m3": material.Density,
            "rgba": list(material.ColorValue),
        },
        "parameter_order": [role_by_id[node.Identity] for node in nodes],
        "parameters": parameters,
    }
    spec = validate(result)
    prism = model.Bodies[0].History.Model
    require(
        all(
            math.isclose(model_value, value, rel_tol=1e-12, abs_tol=0.0)
            for model_value, value in zip(
                (prism.Width, prism.Depth, prism.Height),
                (spec.WidthMm, spec.DepthMm, spec.LengthMm),
                strict=True,
            )
        ),
        "Saved driving literals disagree with the solved cuboid",
    )
    return result
