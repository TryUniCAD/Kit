from dataclasses import asdict
from pathlib import PureWindowsPath

from PlanarRegistryBuild import require

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.AsmDisplayIn import AsmDisplayIn
from convert.adapters.solidworks.Assembly.Display.ReadAsmDisplay import ReadAsmDisplay
from convert.adapters.solidworks.Assembly.Display.ReadDisplayXml import KDisplayNs
from convert.adapters.solidworks.Container.Format import KComponentTreeStream, KeywordsStream
from convert.adapters.solidworks.Core.Native import ParseXml
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName


VISUALS = "ThirdPtyStore/VisualStates"


def header_text(owner, field):
    handle = owner.FieldsValue["shared"][field]
    value = handle.FieldsValue["value"]
    require(handle.ClassValue.NameValue == "moCStringHandle_c" and type(value) is CStringValue
            and value.IsUnicode and handle.FieldsValue["text"] == value.TextValue,
            "parent header has ambiguous typed self-file text")
    return value.TextValue


def observe(archive, *, stem, destination=None, tree_bytes=None):
    link = ReadNativeLink(archive, 0)
    model = link.ConfigValue.RootValue
    native_name = ReadNativeName(model)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000).RootValue.FieldsValue
    configuration = manager["f360"]
    require(configuration is manager["f368"] and configuration.FieldsValue["f08"] == 0,
            "assembly identity requires its actual selected configuration")
    config_name = ReadNativeName(configuration)
    headers = (link.ConfigValue.HeaderValue, ReadHeaderGraph(archive.require("Header2"), 19000))
    file_roles = []
    for header in headers:
        owner = header.FieldsValue["f38"]
        stored = owner.FieldsValue["file"]
        internal, locator = header_text(owner, "h10"), header_text(owner, "h18")
        require(owner.ClassValue.NameValue == "moExtObject_c"
                and owner.FieldsValue["shared"]["f20"] == stored.KindValue == 3
                and owner.FieldsValue["refcfg"]["f10"] == configuration.FieldsValue["f08"]
                and internal == stored.NameValue == native_name and stored.ConfigValue == config_name
                and locator == stored.PathValue == (destination if destination is not None else ""),
                "assembly header does not retain the independent model configuration and file roles")
        file_roles.append({"model": internal, "configuration": stored.ConfigValue, "path_empty": not locator})
    data = archive.require(KComponentTreeStream) if tree_bytes is None else tree_bytes
    tree = ParseXml(data)
    configuration_row, = tree.findall("sw:swConfigurationList/sw:swConfiguration", KDisplayNs)
    models = tree.findall("sw:swModelList/sw:swModel", KDisplayNs)
    model_row, = (row for row in models if row.get("id") == configuration_row.get("swModelRef"))
    file_row, = (row for row in tree.findall("sw:swHeader/sw:swFile", KDisplayNs)
                 if row.get("id") == model_row.get("swFileRef"))
    locator = file_row.attrib["swPath"]
    file_stem = PureWindowsPath(locator).stem
    require(file_row.attrib["swDocType"] == "ASSEMBLY" and file_stem == stem
            and PureWindowsPath(locator).suffix.casefold() == ".sldasm"
            and (destination is None or locator == destination)
            and len(models) == 2 and all(row.attrib["swName"] == file_stem for row in models)
            and configuration_row.attrib["swReference"] == native_name
            and configuration_row.attrib["swName"] == config_name
            and ParseXml(archive.require(KeywordsStream)).attrib["Name"] == native_name,
            "assembly external locator or owned XML and keyword identity differs")
    view = ReadAsmDisplay(archive, tree)
    return {
        "native_model": native_name, "file_stem": file_stem, "configuration": config_name,
        "configuration_reference": configuration_row.attrib["swReference"],
        "keyword_model": native_name, "header_files": file_roles,
        "xml_file_name": PureWindowsPath(locator).name, "xml_model_captions": [row.attrib["swName"] for row in models],
        "view": asdict(view) if view is not None else None,
    }


def request_view(source, actual):
    require(actual["configuration"] == source.configurations[0].name,
            "strict source configuration does not agree with the exact binary model")
    typed, = source.assembly.attributes["typed_display_states"]
    view = actual["view"]
    members = view["MemberValues"]
    require(typed["name"] == view["StateName"]
            and (typed["list_object_id"], typed["state_object_id"]) == (view["ListObjectId"], view["StateObjectId"])
            and [(row["native_feature_id"], row["visible"]) for row in typed["visibility"]]
            == [(row["FeatureId"], row["Visible"]) for row in members]
            and tuple(row["NativeName"] for row in members) == tuple(item.name for item in source.assembly.instances),
            "caller visibility does not join the exact admitted XML and binary owners")
    return {"name": view["StateName"], "visibility": [(row["NativeName"], row["Visible"]) for row in members]}


def xml_display(bundle, request):
    from para.concentric.MakeDisplayTree import DisplayListIntent, DisplayStateIntent, make_display_tree

    require(set(request) == {"name", "visibility"} and type(request["name"]) is str
            and type(request["visibility"]) is list
            and all(type(row) is list and len(row) == 2 and type(row[0]) is str and row[1] is True
                    for row in request["visibility"]), "source display intent requires one ordered all-visible state")
    refs = bundle.OccurrenceValues
    names = tuple(ReadNativeName(node) for node in refs)
    require(tuple(row[0] for row in request["visibility"]) == names,
            "source display intent must own the actual generated occurrences in order")
    actual = tuple((node.FieldsValue["f08"], visible)
                   for node, (_, visible) in zip(refs, request["visibility"], strict=True))
    config = bundle.StateValue.CurrentConfig.FieldsValue["f08"]
    display = AsmDisplayIn(request["name"], tuple(tuple(row) for row in request["visibility"]))
    intent = DisplayListIntent(config, (DisplayStateIntent(request["name"], actual),))
    xml = make_display_tree(bundle.StateValue, bundle.HeaderValue, bundle.ChildValue, refs, intent)
    return xml, display


def source_visuals(parent, child):
    from para.concentric.AuditConcentricDisplayState import bind_visual, model_inputs, xml_owner
    from para.concentric.ProveVisualStateStore import registry, replay

    refs, configuration, config_name, planes, header = model_inputs(parent)
    index = xml_owner(ParseXml(parent.require(KComponentTreeStream)), refs, configuration, config_name, True)
    reg = registry()
    _, _, parent_proof = bind_visual(parent.require(VISUALS), reg, parent, configuration, index, refs, planes, header)
    doc, child_proof = replay(child, reg)
    state = doc.head["root"].f
    holders = [row for row in state["f78"] if row["ref"].ClassValue.NameValue == "moCompHolder_c"]
    (holder,) = holders
    (properties,) = [item["o"] for row in holder["attrs"] for item in row["objs"]
                     if item["o"].ClassValue.NameValue == "visStateVisualPropertiesAttribute_c"]
    appearance = properties.FieldsValue["f10"]
    material = appearance.FieldsValue["f20"]["f90"]
    require(appearance.ClassValue.NameValue == "moVisualProperties_c" and material is not None,
            "child appearance holder lacks its actual populated material")
    return {
        "parent": parent_proof, "child": {**child_proof, "context_count": state["n_comps"],
        "feature_count": state["n_ents"], "state": state["f0f0"], "holder_class": holder["ref"].ClassValue.NameValue,
        "appearance_class": appearance.ClassValue.NameValue,
        "appearance_owner": "moCompHolder_c row -> visStateVisualPropertiesAttribute_c.f10 -> moVisualProperties_c.f20.f90",
        "holder_material_id_words": [material["f00"], material["f04"]]},
    }
