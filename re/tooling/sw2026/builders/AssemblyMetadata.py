from __future__ import annotations

from pathlib import PureWindowsPath
from xml.etree.ElementTree import Element, SubElement, tostring

from convert.adapters.solidworks.Container.Format import COMPONENT_TREE_STREAM, KEYWORDS_STREAM

from builders.Metadata import FILE_VERSION, PRINCIPAL_KEYWORD_ROLES, integer, text


_SCHEMA = "http://www.solidworks.com/sw2003/schema"
_DECLARATION = b'<?xml version="1.0" encoding="UTF-8"?>\r\n'
_IDENTITY_BASIS = (1, 0, 0, 0, 1, 0, 0, 0, 1)
_FEATURE_TYPES = {
    "moCommentsFolder_c": ("Feature", "Comments"),
    "moFavoriteFolder_c": ("Feature", "Favorites"),
    "moHistoryFolder_c": ("Feature", "History"),
    "moSelectionSetFolder_c": ("Feature", "Selection Sets"),
    "moSensorFolder_c": ("Feature", "Sensors"),
    "moLiveSectionFolder_c": ("Feature", "Live Section Planes"),
    "moDocsFolder_c": ("Feature", "Design Binder"),
    "moDetailCabinet_c": ("Feature", "Annotations"),
    "moEnvFolder_c": ("Feature", "Lights and Cameras"),
    "moInkMarkupFolder_c": ("Feature", "Markups"),
    "moEqnFolder_c": ("Feature", "Equations"),
    **PRINCIPAL_KEYWORD_ROLES,
    "moMateGroup_c": ("Feature", "Mates"),
}


def _xml(root):
    return _DECLARATION + tostring(root, encoding="utf-8").replace(b" />", b"/>") + b"\r\n"


def _path(file_record, suffix):
    path = PureWindowsPath(text(file_record["h18"]["f08"], "assembly XML file path"))
    if path.suffix.casefold() != suffix or not path.stem:
        raise ValueError(f"assembly XML indexes require a {suffix} file identity")
    return path


def _coordinates(values):
    return " ".join(format(value, ".16g") for value in values)


def _transform(reference):
    transform = reference["f360"]
    basis = tuple(transform["f08"][f"m{i}"] for i in range(9)) if transform["has_matrix"] else _IDENTITY_BASIS
    position = tuple(transform[key] for key in ("f58", "f60", "f68"))
    if transform["f70"] != 1.0:
        raise ValueError("assembly XML indexes require unit-scale rigid placements")
    return _coordinates((*basis[:3], 0, *basis[3:6], 0, *basis[6:], 0, *position, 1))


def _occurrence_name(reference):
    name = reference["f18"]["f08"]
    base, separator, number = name.rpartition("-")
    if not base or not separator or not number.isascii() or not number.isdecimal() or number.startswith("0") or len(number) > 10:
        raise ValueError("assembly XML indexes require a nonempty occurrence name with a canonical positive decimal suffix")
    integer(int(number), "component reference number", low=1, high=0x7FFFFFFF)
    return base, number


def _model_attributes(configuration, *, document_id, file_id, name, stamp):
    flags = integer(configuration["f4c4"], "configuration flags")
    signed_flags = flags - (1 << 32) if flags & (1 << 31) else flags
    return {
        "id": str(document_id),
        "swName": name,
        "swConfigurationName": configuration["f18"]["f08"],
        "swConfigurationId": str(configuration["f08"]),
        "swLastModifiedStamp": str(stamp),
        "swConfigurationFlags": str(signed_flags),
        "swFileRef": str(file_id),
    }


def _file_node(header, *, file_id, kind, path, record):
    SubElement(header, "swFile", {
        "id": str(file_id), "swDocType": kind,
        "swCreationTime": str(record["f28"]), "swPath": str(path),
    })


def _reference_node(root, *, object_id, reference, child_id):
    base, number = _occurrence_name(reference)
    configuration = reference["f3c0"]
    SubElement(root, "swReference", {
        "id": str(object_id), "swName": base, "swReferenceNumber": number,
        "swComponentReference": "", "swComponentName": base,
        "swID": str(reference["f08"]), "swIsVirtualComponent": "NO",
        "swConfigurationId": str(configuration["f10"]),
        "swConfigurationName": configuration["f08"],
        "swSuppressed": "NO", "swHidden": "NO", "swFlexible": "NO",
        "swExcludeFromBOM": "NO", "swZone": "NO",
        "swModelRef": str(child_id), "swTransform": _transform(reference),
        "swTransformStamp": str(reference["f3f0"]),
    })


def _instance_tree(*, model, configuration, root_file, root_path, references, child, child_file, child_path):
    count = len(references)
    document_count = 1 if child is None else 2
    object_count = 1 + 2 * document_count + count
    root = Element("swSolidWorks", {"xmlns": _SCHEMA, "swObjCount": str(object_count), "swVersion": str(FILE_VERSION)})
    header = SubElement(root, "swHeader", {"swObjCount": str(document_count), "swSavedInLDREditMode": "NO"})
    models = SubElement(root, "swModelList", {"swObjCount": str(document_count)})
    _file_node(header, file_id=3, kind="ASSEMBLY", path=root_path, record=root_file)
    if child is not None:
        _file_node(header, file_id=6, kind="PART", path=child_path, record=child_file)
        SubElement(models, "swModel", _model_attributes(child.configuration, document_id=5, file_id=6, name=root_path.stem, stamp=references[0]["f3e0"]))
    owner_attrs = _model_attributes(configuration, document_id=2, file_id=3, name=root_path.stem, stamp=configuration["f860"])
    if model["has_f1a18"]:
        bounds = model["f1a18"]
        owner_attrs["swBoundingBox"] = _coordinates(bounds[f"b{i}"] for i in (6, 7, 8, 3, 4, 5))
    owner_attrs["swAssemblyFeatureEffectedComponents"] = ""
    owner = SubElement(models, "swModel", owner_attrs)
    for index, reference in enumerate(references):
        _reference_node(owner, object_id=4 if index == 0 else index + 6, reference=reference, child_id=5)
    configurations = SubElement(root, "swConfigurationList", {"swObjCount": "1"})
    needs_rebuild = configuration["f968"] != 1 and bool(configuration["f0c"] & 8)
    SubElement(configurations, "swConfiguration", {
        "id": "1", "swName": configuration["f18"]["f08"], "swID": str(configuration["f08"]),
        "swReference": model["f18"]["f08"], "swMostRecentConfiguration": "YES",
        "swConfigurationNeedsUpdate": "YES" if needs_rebuild else "NO",
        "swDefeatureConfiguration": "NO", "swModelRef": "2",
    })
    SubElement(root, "swExtFeatureList", {"swObjCount": "0"})
    return _xml(root)


def _keywords(*, model, configuration, root_file, features, references, child_path):
    root = Element("Keywords", {"id": str(root_file["f28"]), "Name": model["f18"]["f08"]})
    SubElement(root, "Configuration", {
        "id": str(configuration["f08"]), "Name": configuration["f18"]["f08"], "Type": "ConfigurationManager",
    })
    entries = [(_FEATURE_TYPES[node.cls], node) for node in features]
    if references:
        entries.extend((("Reference", child_path.stem + "-"), node) for node in references)
    for (tag, kind), node in sorted(entries, key=lambda row: (row[0][0], str(row[1]["f08"]))):
        SubElement(root, tag, {"id": str(node["f08"]), "Name": node["f18"]["f08"], "Type": kind})
    return b"\x86" + _xml(root)


def assembly_xml_streams(*, model, configuration, model_header, features, child):
    if model.cls != "moAssembly_c" or configuration.cls != "moConfiguration_c" or configuration["owner"] is not model:
        raise ValueError("assembly XML indexes require an ordinary assembly with its active configuration")
    if model_header["f38"] is None:
        raise ValueError("assembly XML indexes require an explicit assembly output file identity")
    root_file = model_header["f38"]["shared"]
    root_path = _path(root_file, ".sldasm")
    references = tuple(row["o"] for row in model["f68"]["list"]["items"]) if model["has_list68"] else ()
    if len(references) != model["f1560"] or bool(references) != (child is not None):
        raise ValueError("assembly XML indexes require exactly the constructed occurrences")
    child_file = None
    child_path = None
    if child is not None:
        child_file = child.model_header["f38"]["shared"]
        child_path = _path(child_file, ".sldprt")
        child_key = {"f08": child.configuration["f18"]["f08"], "f10": child.configuration["f08"]}
        directory = model_header["f30"]["items"][0]["o"]
        if any(reference.cls != "moReference_c" or reference["owner"] is not model or reference["f3b0"] is not directory or reference["f3c0"] != child_key or reference["f3e0"] != child.model_header["f40"] for reference in references):
            raise ValueError("assembly XML indexes require direct references to one generated part and configuration")
        if len({_occurrence_name(reference) for reference in references}) != len(references):
            raise ValueError("assembly XML indexes require distinct occurrence names and reference numbers")
    if any(node.cls not in _FEATURE_TYPES for node in features):
        raise ValueError("assembly keyword index contains an unclassified feature role")
    tree = _instance_tree(model=model, configuration=configuration, root_file=root_file, root_path=root_path, references=references, child=child, child_file=child_file, child_path=child_path)
    keywords = _keywords(model=model, configuration=configuration, root_file=root_file, features=features, references=references, child_path=child_path)
    return {COMPONENT_TREE_STREAM: tree, KEYWORDS_STREAM: keywords}
