from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput


FREECAD_DEFAULT_MATERIAL = "7f9fd73b-50c9-41d8-b7b2-575a030c1eeb"
RELEASE_EXTENSIONS = {
    "0.21": ("AttachExtension",),
    "1.0": ("SuppressibleExtension", "AttachExtension"),
    "1.1": ("SuppressibleExtension", "AttachExtension", "PreviewExtension"),
}
FEATURE_PROPERTIES = {"AttacherEngine", "AttachmentSupport", "ShapeMaterial", "Suppressed", "SuppressedShape"}
FEATURE_SCALARS = {"AttacherEngine", "Suppressed"}
BODY_PROPERTIES = {"AllowCompound", "ShapeMaterial"}
DOCUMENT_PROPERTIES = {"UnitSystem", "UseHasher"}


def require(value, message):
    if not value:
        raise ValueError(message)


def child(prop, kind, tag):
    require(prop["tag"] == "Property" and prop["attributes"]["type"] == "App::Property" + kind,
            f"FreeCAD property has a different type for {prop['attributes']['name']}")
    values = prop["children"]
    require(len(values) == 1 and values[0]["tag"] == tag, "FreeCAD property shape differs from the documented object")
    return values[0]


def value(properties, name, kind, tag):
    return child(properties[name], kind, tag)["attributes"]["value"]


def release(version):
    if version.startswith("0.21"):
        return "0.21"
    return {
        "1.0R39319 (Git)": "1.0",
        "1.1R20260928 (Git shallow)": "1.1",
    }.get(version)


def extensions(version):
    return [
        {"attributes": {"name": name, "type": ("App::" if name == "SuppressibleExtension" else "Part::") + name},
         "tag": "Extension"}
        for name in RELEASE_EXTENSIONS[version]
    ]


def caption(properties, name):
    outer = properties[name]
    require(outer["tag"] == "Property" and outer["attributes"]["type"] == "App::PropertyEnumeration",
            "FreeCAD named enumeration has another type")
    index, items = outer["children"]
    require(index["tag"] == "Integer" and index["attributes"]["CustomEnum"] == "true"
            and items["tag"] == "CustomEnumList", "FreeCAD named enumeration has another layout")
    selected = int(index["attributes"]["value"])
    choices = items["children"]
    require(int(items["attributes"]["count"]) == len(choices) and 0 <= selected < len(choices)
            and all(row["tag"] == "Enum" and type(row["attributes"]["value"]) is str for row in choices),
            "FreeCAD named enumeration contains an invalid selector")
    return choices[selected]["attributes"]["value"]


def material_id(properties):
    row = properties["ShapeMaterial"]
    require(row["tag"] == "Property" and row["attributes"]["type"] == "Materials::PropertyMaterial",
            "FreeCAD shape material has another property type")
    material, = row["children"]
    require(material["tag"] == "PropertyMaterial"
            and material["attributes"] == {"uuid": FREECAD_DEFAULT_MATERIAL}
            and not material.get("children"), "FreeCAD box uses an unqualified material assignment")
    return material["attributes"]["uuid"]


def cache_document(original):
    value = original["string_hasher"]
    require(value == {
        "attribute": "1", "entries": [],
        "nodes": [{"attributes": {"count": "0", "saveall": "0", "threshold": "0"}, "tag": "StringHasher"}],
    }, "FreeCAD document has a populated string map")


def document_units(properties):
    unit = caption(properties, "UnitSystem")
    hasher = value(properties, "UseHasher", "Bool", "Bool")
    require(unit == "Standard (mm, kg, s, °)" and hasher == "true",
            "FreeCAD box has an unqualified document unit or string hasher mode")
    return UnitInput("mm", "degree", "custom", 4, "kg"), {
        "FreeCAD Unit System": unit, "FreeCAD Use Hasher": hasher,
    }
