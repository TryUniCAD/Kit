# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
import sys
from pathlib import Path

from convert.Formats.Fusion.DocumentCodec.Materials.CheckMaterial import CheckMaterial
from convert.Formats.Fusion.DocumentCodec.Materials.Model.DirectionValue import DirectionValue
from convert.Formats.Fusion.DocumentCodec.Materials.Model.FinishSpec import FinishSpec
from convert.Formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import MaterialSpec
from convert.Formats.Fusion.DocumentCodec.Materials.Model.MechanicSpec import MechanicSpec
from convert.Formats.Fusion.DocumentCodec.Materials.Model.ThermalSpec import ThermalSpec
from convert.Formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue

RESEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RESEARCH / "SavedConfigEnvelope"))
import ConfigRequest as Config
from GenerateSemantic import exact_fields, label, number, require

SCHEMA = 1
SCOPE = "fixed_cuboid_authored_material_properties"
OPEN_SCOPE = [name for name in Config.OPEN_SCOPE if name != "saved_appearance_and_material_graph"] + [
    "saved_material_compatibility_aliases_resources_and_unknown_schemas",
]
MECHANICS = {
    "conductivity_w_m_k": "Conductivity",
    "specific_heat_j_kg_k": "SpecificHeat",
    "damping": "Damping",
}
METAL_MECHANICS = {
    "young_modulus_pa": "YoungModulus",
    "poisson_ratio": "PoissonRatio",
    "shear_modulus_pa": "ShearModulus",
    "yield_strength_pa": "YieldStrength",
    "tensile_strength_pa": "TensileStrength",
    "expansion_per_k": "Expansion",
}
DIRECTIONS = ("1", "2", "X", "Y", "Z")
THERMAL = {
    "density_kg_m3": "Density",
    "conductivity_w_m_k": "Conductivity",
    "specific_heat_j_kg_k": "SpecificHeat",
    "emissivity": "Emissivity",
    "resistivity_ohm_m": "Resistivity",
    "permeability": "Permeability",
    "porosity": "Porosity",
    "reflectivity": "Reflectivity",
}
FINISH = {"roughness": "Roughness", "anisotropy": "Anisotropy", "rotation": "Rotation"}
OPAQUE = ("reflectance", "translucent", "scatter_distance_mm", "scatter_color_rgba")
EXTERIOR = ("name", "kind", "color_space", "tint_rgba", *FINISH)


def numbers(row, mapping):
    return {sdk: number(row[key], key) for key, sdk in mapping.items()}


def projected_numbers(spec, mapping):
    return {key: getattr(spec, sdk) for key, sdk in mapping.items()}


def rgba(value, name):
    require(type(value) is list and len(value) == 4, f"{name} requires four RGBA components")
    return ColorValue(*(number(channel, name) for channel in value))


def channels(value):
    return [value.RedValue, value.GreenValue, value.BlueValue, value.AlphaValue]


def flag(value, name):
    require(type(value) is bool, f"{name} requires a boolean")
    return value


def mechanic_spec(row, metal):
    if not metal:
        return MechanicSpec(**numbers(exact_fields(row, MECHANICS, "mechanics"), MECHANICS))
    mapping = MECHANICS | METAL_MECHANICS
    exact_fields(row, (*mapping, "behavior", "directional_expansion_per_k"), "mechanics")
    behavior = row["behavior"]
    require(behavior == "Isotropic", "Only isotropic Metal mechanics are supported")
    overrides = row["directional_expansion_per_k"]
    require(type(overrides) is dict and overrides.keys() <= set(DIRECTIONS), "Unknown expansion direction")
    return MechanicSpec(
        **numbers(row, mapping),
        Behavior=behavior,
        Directional=tuple(
            DirectionValue("Expansion", direction, number(overrides[direction], f"expansion {direction}"))
            for direction in DIRECTIONS
            if direction in overrides
        ),
    )


def thermal_spec(row, metal):
    if not metal:
        require(row is None, "Basic structure requires null thermal data")
        return None
    exact_fields(row, (*THERMAL, "transmits_light"), "thermal")
    return ThermalSpec(
        **numbers(row, THERMAL), TransmitsLight=flag(row["transmits_light"], "transmits_light")
    )


def finish_spec(row, metal):
    exact_fields(row, EXTERIOR if metal else (*EXTERIOR, *OPAQUE), "finish")
    require(row["kind"] == ("metal" if metal else "opaque"), "Unsupported finish family")
    space = row["color_space"]
    require(type(space) is int and space in (0, 1), "Expected a supported integer finish color space")
    additional = {}
    if not metal:
        distance = row["scatter_distance_mm"]
        additional = {
            "Reflectance": number(row["reflectance"], "reflectance"),
            "Translucent": flag(row["translucent"], "translucent"),
            "ScatterDistance": None if distance is None else number(distance, "scatter_distance_mm"),
            "ScatterColor": rgba(row["scatter_color_rgba"], "scatter_color_rgba"),
        }
    return FinishSpec(
        **numbers(row, FINISH),
        **additional,
        NameValue=label(row["name"], "finish name"),
        Metallic=metal,
        ColorSpace=space,
        Tint=rgba(row["tint_rgba"], "tint_rgba"),
    )


def validate(request):
    exact_fields(request, ("schema", "scope", "configuration_request", "material_properties"), "request")
    require(
        type(request["schema"]) is int and request["schema"] == SCHEMA and request["scope"] == SCOPE,
        "Unsupported authored material request schema",
    )
    configuration = Config.validate(request["configuration_request"])
    wrapper = request["material_properties"]
    exact_fields(
        wrapper,
        ("structural_class", "type", "mechanics", "thermal", "finish", "component_default"),
        "material_properties",
    )
    require(
        (wrapper["structural_class"], wrapper["type"]) in (("Basic", "Generic"), ("Metal", "Metal")),
        "Unsupported structural class and physical material type",
    )
    base = Config.Cameras.validate_cuboid(configuration["camera_request"]["cuboid"]).Material
    metal = wrapper["structural_class"] == "Metal"
    material = MaterialSpec(
        base.NameValue,
        base.Density,
        base.Color,
        wrapper["structural_class"],
        mechanic_spec(wrapper["mechanics"], metal),
        thermal_spec(wrapper["thermal"], metal),
        finish_spec(wrapper["finish"], metal),
        wrapper["type"],
    )
    CheckMaterial(material)
    return configuration, material, flag(wrapper["component_default"], "component_default")


def material_properties(material, component_default):
    metal = material.ClassName == "Metal"
    mechanics = projected_numbers(material.Mechanics, MECHANICS)
    if metal:
        mechanics.update(projected_numbers(material.Mechanics, METAL_MECHANICS))
        mechanics["behavior"] = material.Mechanics.Behavior
        mechanics["directional_expansion_per_k"] = {
            override.Direction: override.Value
            for override in material.Mechanics.Directional
            if override.FieldKey == "Expansion"
        }
    thermal = material.Thermal
    finish = material.Finish
    result = {
        "name": finish.NameValue,
        "kind": "metal" if finish.Metallic else "opaque",
        "color_space": finish.ColorSpace,
        "tint_rgba": channels(finish.Tint),
        **projected_numbers(finish, FINISH),
    }
    if not metal:
        result.update(
            reflectance=finish.Reflectance,
            translucent=finish.Translucent,
            scatter_distance_mm=finish.ScatterDistance,
            scatter_color_rgba=channels(finish.ScatterColor),
        )
    return {
        "structural_class": material.ClassName,
        "type": material.TypeName,
        "component_default": component_default,
        "mechanics": mechanics,
        "thermal": (
            None
            if thermal is None
            else {**projected_numbers(thermal, THERMAL), "transmits_light": thermal.TransmitsLight}
        ),
        "finish": result,
    }


def canonical_properties(material, component_default):
    return json.dumps(
        material_properties(material, component_default),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
