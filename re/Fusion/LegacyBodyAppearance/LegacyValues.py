"""Author the bounded legacy Generic body property streams from explicit values."""

from math import isfinite
from re import compile

from convert.Formats.Fusion.MaterialCodec.Limits import KMaxCount, KMaxString
from convert.Formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from convert.Formats.Fusion.MaterialCodec.Models.PropertySpec import PropertySpec
from convert.Formats.Fusion.MaterialCodec.Models.PropertyValue import PropertyValue
from convert.Formats.Fusion.MaterialCodec.Records.EncodeFields import EncodeFields


def _wire(name, kind, *, definition=False, multiple=False, single_link=False):
    return PropertySpec(
        name,
        kind,
        IsDefinition=definition,
        IsMultiple=multiple,
        ConnectMode="single" if single_link else "none",
    )


_BASE_SCHEMA = _wire("BaseSchema", "String", definition=True)
_GROUPS = {
    "definition": {
        "hidden": _wire("Hidden", "Boolean", definition=True),
        "ui_name": _wire("UIName", "String", definition=True),
        "version_symbol": _wire("VersionGUID", "Uuid", definition=True),
        "categories": _wire("category", "String", definition=True, multiple=True),
        "description": _wire("description", "String", definition=True),
        "keywords": _wire("keyword", "String", definition=True, multiple=True),
        "thumbnail": _wire("thumbnail", "URL", definition=True, multiple=True),
    },
    "metadata": {
        "library_symbol": _wire("AssetLibID", "String"),
        "exchange_guid": _wire("ExchangeGUID", "Uuid"),
        "shared_asset_code": _wire("common_Shared_Asset", "Choice"),
        "mode": _wire("mode", "Integer"),
        "revision": _wire("revision", "Integer"),
        "swatch": _wire("swatch", "String"),
        "version": _wire("version", "Integer"),
    },
    "diffuse_tint": {
        "color_by_object": _wire("color_by_object", "Boolean"),
        "tint_rgba": _wire("common_Tint_color", "Color"),
        "tint_color_space": _wire("common_Tint_color_colorspace", "Choice"),
        "tint_enabled": _wire("common_Tint_toggle", "Boolean"),
        "diffuse_rgba": _wire("generic_diffuse", "Color", single_link=True),
        "diffuse_color_space": _wire("generic_diffuse_colorspace", "Choice"),
        "diffuse_image_fade": _wire("generic_diffuse_image_fade", "Float"),
    },
    "reflection_transmission": {
        "glossiness": _wire("generic_glossiness", "Float", single_link=True),
        "metal": _wire("generic_is_metal", "Boolean"),
        "reflection_depth": _wire("generic_refl_depth", "Integer"),
        "reflection_glossy_samples": _wire("generic_reflection_glossy_samples", "Integer"),
        "reflectivity_at_0deg": _wire("generic_reflectivity_at_0deg", "Float", single_link=True),
        "reflectivity_at_90deg": _wire("generic_reflectivity_at_90deg", "Float", single_link=True),
        "refraction_depth": _wire("generic_refr_depth", "Integer"),
        "refraction_glossy_samples": _wire("generic_refraction_glossy_samples", "Integer"),
        "refraction_index": _wire("generic_refraction_index", "Float"),
        "refraction_translucency_weight": _wire(
            "generic_refraction_translucency_weight", "Float", single_link=True
        ),
        "transparency": _wire("generic_transparency", "Float", single_link=True),
        "transparency_image_fade": _wire("generic_transparency_image_fade", "Float"),
    },
    "ambient_occlusion_edges": {
        "details": _wire("generic_ao_details", "Boolean"),
        "distance": _wire("generic_ao_distance", "Float"),
        "enabled": _wire("generic_ao_on", "Boolean"),
        "samples": _wire("generic_ao_samples", "Integer"),
        "backface_cull": _wire("generic_backface_cull", "Boolean"),
        "roundcorners_allow_different_materials": _wire(
            "generic_roundcorners_allow_different_materials", "Boolean"
        ),
        "roundcorners_radius": _wire("generic_roundcorners_radius", "Float", single_link=True),
    },
    "emission_normal": {
        "bump_amount": _wire("generic_bump_amount", "Float", single_link=True),
        "bump_rgba": _wire("generic_bump_map", "Color", single_link=True),
        "cutout_opacity": _wire("generic_cutout_opacity", "Float", single_link=True),
        "color_temperature": _wire("generic_self_illum_color_temperature", "Float"),
        "filter_rgba": _wire("generic_self_illum_filter_map", "Color", single_link=True),
        "filter_color_space": _wire("generic_self_illum_filter_map_colorspace", "Choice"),
        "luminance": _wire("generic_self_illum_luminance", "Float"),
    },
}
WIRE_FIELDS = tuple(
    sorted(
        (_BASE_SCHEMA, *(field for group in _GROUPS.values() for field in group.values())),
        key=lambda field: field.FieldName,
    )
)
_REQUEST_KEYS = {"schema", "scope", *_GROUPS}
_SCOPE = "legacy_generic_body_wire_values"
_SYMBOL = compile(r"research:[A-Za-z0-9][A-Za-z0-9_.-]*")


def _exact_object(value, expected, label):
    if type(value) is not dict:
        raise ValueError(f"{label} must be an object")
    missing = expected - value.keys()
    unexpected = value.keys() - expected
    if missing or unexpected:
        details = []
        if missing:
            details.append(f"missing {', '.join(sorted(map(repr, missing)))}")
        if unexpected:
            details.append(f"unexpected {', '.join(sorted(map(repr, unexpected)))}")
        raise ValueError(f"{label} fields do not match ({', '.join(details)})")
    return value


def _text(value, label):
    if type(value) is not str or len(value) > KMaxString or "\0" in value:
        raise ValueError(f"{label} must be bounded UTF-8 text without NUL")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError(f"{label} must be bounded UTF-8 text without NUL") from error
    if len(encoded) > KMaxString:
        raise ValueError(f"{label} must be bounded UTF-8 text without NUL")
    return value


def _finite_float(value, label):
    if type(value) is not float or not isfinite(value):
        raise ValueError(f"{label} must be a finite binary64 number")
    return value


def _value(value, field, key, label):
    if key == "thumbnail":
        if type(value) is not list or value:
            raise ValueError(f"{label} must be an empty array in this wire profile")
        return ()
    if key in {"exchange_guid", "swatch"}:
        if type(value) is not str or value:
            raise ValueError(f"{label} must be empty text in this wire profile")
        return value
    if key in {"library_symbol", "version_symbol"}:
        symbol = _text(value, label)
        if _SYMBOL.fullmatch(symbol) is None:
            raise ValueError(f"{label} must be a research: symbol")
        return symbol
    if field.IsMultiple:
        if type(value) is not list or len(value) > KMaxCount:
            raise ValueError(f"{label} must be a bounded text array")
        return tuple(_text(entry, f"{label}[{index}]") for index, entry in enumerate(value))
    match field.ValueKind:
        case "String":
            return _text(value, label)
        case "Float":
            return _finite_float(value, label)
        case "Boolean":
            if type(value) is not bool:
                raise ValueError(f"{label} must be a boolean")
            return value
        case "Integer" | "Choice":
            if type(value) is not int or not -(2**31) <= value < 2**31:
                raise ValueError(f"{label} must be a signed 32-bit integer")
            if field.ValueKind == "Choice":
                choices = (0, 1) if key == "shared_asset_code" else (0, 1, 2)
                if value not in choices:
                    raise ValueError(f"{label} must be one of {choices}")
            return value
        case "Color":
            if type(value) is not list or len(value) != 4:
                raise ValueError(f"{label} must be a four-channel RGBA array")
            return ColorValue(
                *(_finite_float(channel, f"{label}[{index}]") for index, channel in enumerate(value))
            )
    raise ValueError(f"{label} has an unsupported wire kind")


def build_legacy_values(request: object) -> tuple[bytes, bytes]:
    """Return the definition and instance property bytes for the research wire profile."""
    request = _exact_object(request, _REQUEST_KEYS, "legacy body request")
    if type(request["schema"]) is not int or request["schema"] != 1 or request["scope"] != _SCOPE:
        raise ValueError(f"legacy body request requires schema 1 and scope {_SCOPE!r}")
    definition_values = [PropertyValue(_BASE_SCHEMA.FieldName, "GenericSchema")]
    instance_values = []
    for group_name, fields in _GROUPS.items():
        group = _exact_object(request[group_name], fields.keys(), group_name)
        for key, field in fields.items():
            value = _value(group[key], field, key, f"{group_name}.{key}")
            destination = definition_values if field.IsDefinition else instance_values
            destination.append(PropertyValue(field.FieldName, value))
    return (
        EncodeFields(WIRE_FIELDS, tuple(definition_values), True),
        EncodeFields(WIRE_FIELDS, tuple(instance_values), False),
    )
