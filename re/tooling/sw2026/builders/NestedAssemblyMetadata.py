from __future__ import annotations

from xml.etree.ElementTree import Element, SubElement

from builders.AssemblyMetadata import _FEATURE_TYPES, _SCHEMA, _coordinates, _file_node, _model_attributes, _path, _reference_node, _xml
from builders.Metadata import FILE_VERSION
from convert.adapters.solidworks.Container.Format import COMPONENT_TREE_STREAM, KEYWORDS_STREAM


def nested_assembly_xml(*, root):
    identities = {}
    files = []
    models = []
    references = {}
    next_id = 2

    def visit(document):
        nonlocal next_id
        if id(document) in identities:
            return identities[id(document)][0]
        model_id, file_id = next_id, next_id + 1
        next_id += 2
        identities[id(document)] = (model_id, file_id)
        files.append(document)
        rows = []
        if document.model.cls == "moAssembly_c":
            for reference, target in document.references:
                reference_id = next_id
                next_id += 1
                target_id = visit(target)
                rows.append((reference_id, reference, target_id))
        references[id(document)] = rows
        models.append(document)
        return model_id

    root_id = visit(root)
    root_path = _path(root.model_header["f38"]["shared"], ".sldasm")
    xml = Element("swSolidWorks", {"xmlns": _SCHEMA, "swObjCount": str(next_id - 1), "swVersion": str(FILE_VERSION)})
    header = SubElement(xml, "swHeader", {"swObjCount": str(len(files)), "swSavedInLDREditMode": "NO"})
    listing = SubElement(xml, "swModelList", {"swObjCount": str(len(models))})
    for document in files:
        _, file_id = identities[id(document)]
        assembly = document.model.cls == "moAssembly_c"
        shared = document.model_header["f38"]["shared"]
        _file_node(header, file_id=file_id, kind="ASSEMBLY" if assembly else "PART", path=_path(shared, ".sldasm" if assembly else ".sldprt"), record=shared)
    for document in models:
        model_id, file_id = identities[id(document)]
        attributes = _model_attributes(document.configuration, document_id=model_id, file_id=file_id, name=root_path.stem,
                                       stamp=document.configuration["f860"])
        if document.model.cls == "moAssembly_c":
            attributes["swBoundingBox"] = _coordinates(document.model["f1a18"][f"b{i}"] for i in (6, 7, 8, 3, 4, 5))
            attributes["swAssemblyFeatureEffectedComponents"] = ""
        model = SubElement(listing, "swModel", attributes)
        for object_id, reference, target_id in references[id(document)]:
            _reference_node(model, object_id=object_id, reference=reference, child_id=target_id)
    configuration = root.configuration
    configurations = SubElement(xml, "swConfigurationList", {"swObjCount": "1"})
    SubElement(configurations, "swConfiguration", {
        "id": "1", "swName": configuration["f18"]["f08"], "swID": str(configuration["f08"]),
        "swReference": root.model["f18"]["f08"], "swMostRecentConfiguration": "YES",
        "swConfigurationNeedsUpdate": "YES" if configuration["f968"] != 1 and configuration["f0c"] & 8 else "NO",
        "swDefeatureConfiguration": "NO", "swModelRef": str(root_id),
    })
    SubElement(xml, "swExtFeatureList", {"swObjCount": "0"})
    keywords = Element("Keywords", {"id": str(root.model_header["f38"]["shared"]["f28"]), "Name": root.model["f18"]["f08"]})
    SubElement(keywords, "Configuration", {"id": str(configuration["f08"]), "Name": configuration["f18"]["f08"], "Type": "ConfigurationManager"})
    entries = [(_FEATURE_TYPES[node.cls], node) for node in root.features]
    for reference, target in root.references:
        suffix = ".sldasm" if target.model.cls == "moAssembly_c" else ".sldprt"
        path = _path(target.model_header["f38"]["shared"], suffix)
        entries.append((("Reference", path.stem + "-"), reference))
    for (tag, kind), node in sorted(entries, key=lambda row: (row[0][0], str(row[1]["f08"]))):
        SubElement(keywords, tag, {"id": str(node["f08"]), "Name": node["f18"]["f08"], "Type": kind})
    return {COMPONENT_TREE_STREAM: _xml(xml), KEYWORDS_STREAM: b"\x86" + _xml(keywords)}
