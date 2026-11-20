from collections.abc import Mapping
from functools import partial
from hashlib import sha256
from subprocess import check_output
import sys
from types import ModuleType

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.ChangeContext import ChangeFlagsMut
from convert.adapters.solidworks.Archive.Bodies.CheckBodyMut import CheckBodyMut
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.GetVirtualRule import GetVirtualRule
from convert.adapters.solidworks.Archive.Bodies.Layouts.ContainerFields import KContainerFields
from convert.adapters.solidworks.Archive.Bodies.Layouts.FeatureFields import KFeatureFields
from convert.adapters.solidworks.Archive.Bodies.Layouts.GeometryFields import KGeometryFields
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteFieldsMut import WriteFieldsMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSchemaMut import WriteSchemaMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue

BASE = "dbfbb09cbe8576b275b01487b8e195d6b00e08be"
AGGREGATE = "2393c3a8106e83ee90e977fb167d27900e5f4f2a"
LAYOUT_PACKAGE = "convert.adapters.solidworks.Archive.Bodies.Layouts."
LAYOUT_ROOT = "src/convert/adapters/solidworks/Archive/Bodies/Layouts/"
PINS = {
    "UserPropFields": "820dabbf56e60f74d509851c07d70f7dc0874864c1bc6bbcc70f980cac2e4102",
    "HeaderBodyFields": "070a2df308656adc58311227485d2b98f8ed898b2fbc8f5fcc52b074b8877caf",
    "ConfigurationFields": "5066c1ef798738bc70492deb29a1aeab181755ddd21eba63874379edadcb6ce9",
    "ExternalFields": "292738d8a389ecfcf5b73648841ad52b34746c04252ec046318683c02c293ddb",
    "MaterialFields": "82283bd6a47ea47829858b732db8751cfff312752fe210859bdde88b19bf0d99",
    "ContainerFields": "f9c9230c4247b400d3e458940fc419f263cd870f420fb5760c6b76fa388b2521",
    "BodyVirtuals": "c4391fe9a98e3c216b6106ca0dc45269603b5d0bf2189f660adff34b2e4e17b8",
    "BodySchemas": "ce531b2725faf12bdad8eaea5d3b2a6b32eaa17c78803c3f96d0e371a7f9b118",
}
LAYOUTS = (
    "mgVector_c.restore", "moBaseConfiguration_c", "moCStringHandle_c",
    "moConcept_c.SerializeLWData", "moConfigurationMgr_c", "moCustomPropertyList",
    "moEntVisProp_c", "moExtObject_c", "moFeature_c", "moFeature_c.SerializeXmlData",
    "moLinkedAtomIdNode_c", "moMassProp_c", "moNodeName_c", "moNode_c.SerializeLWData",
    "moNode_c.SerializeNode", "moPartConfigObject_c", "moPartConfiguration_c",
    "moReferencedConfiguration_c", "moSharedFileDef_c", "moUserProperty_c.restore",
    "moVisProp_c", "moVisualProperties_c", "moVisualProperties_c.restore", "suObList",
    "su_CDWordArray", "su_CMapStringToInt", "su_CStringArray",
    "uoDSPBRProperties_c.restore", "uoMaterialProperties.restore",
    "uoRVAppearanceProperties.restore", "utLineWidth_c.Serialize2",
)
DESCRIPTORS = (
    "moConfigurationMgr_c", "moPartConfiguration_c", "moNodeName_c",
    "moVisualProperties_c", "moLinkedAtomIdNode_c", "moExtObject_c",
    "moCStringHandle_c", "suObList",
)
MANAGER = RuntimeClass("moConfigurationMgr_c", 1)
CONFIGURATION = RuntimeClass("moPartConfiguration_c", 1)
NAME = RuntimeClass("moNodeName_c", 1)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_grammar(repo):
    modules = {}
    support = []
    try:
        for name, expected in PINS.items():
            path = LAYOUT_ROOT + name + ".py"
            raw = check_output(("git", "show", f"{AGGREGATE}:{path}"), cwd=repo)
            require(sha256(raw).hexdigest() == expected, f"aggregate layout changed: {name}")
            module = ModuleType(LAYOUT_PACKAGE + name)
            exec(compile(raw, f"{AGGREGATE}:{path}", "exec"), module.__dict__)
            modules[name] = module
            if name in ("HeaderBodyFields", "UserPropFields"):
                require(module.__name__ not in sys.modules, f"unowned support module: {name}")
                sys.modules[module.__name__] = module
                support.append(module.__name__)
    finally:
        for name in support:
            del sys.modules[name]
    container = modules["ContainerFields"].KContainerFields
    require(all(container[name] == value for name, value in KContainerFields.items()),
            "the aggregate containers differ from already accepted field rules")
    fields = {
        **modules["ConfigurationFields"].KConfigurationFields,
        **modules["ExternalFields"].KExternalFields,
        **modules["MaterialFields"].KMaterialFields,
        **container, **KContainerFields, **KFeatureFields, **KGeometryFields,
    }
    schemas = {name: modules["BodySchemas"].KBodySchemas[name] for name in DESCRIPTORS}
    virtuals = {key: value for key, value in modules["BodyVirtuals"].KBodyVirtuals.items()
                if key[0] in schemas}
    return {name: fields[name] for name in LAYOUTS}, virtuals, schemas


def context_for(version, grammar):
    require(type(version) is int and version == 19000, "part manager requires archive version 19000")
    return BodyContext(version, *grammar)


def as_text(value):
    if isinstance(value, CStringValue):
        return value.TextValue
    if type(value) is tuple and len(value) == 2 and value[0] == "A":
        value = value[1]
    require(type(value) is str, "part manager fields require typed text")
    return value


def node_name(node):
    require(isinstance(node, ArchiveNode) and node.ClassValue == NAME,
            "part manager name requires its schema-one name object")
    value = as_text(node.FieldsValue.get("f08"))
    require(bool(value), "part manager name object cannot be empty")
    return value


def part_owner(root):
    require(isinstance(root, ArchiveNode) and root.ClassValue == MANAGER,
            "part manager requires its schema-one root")
    fields = root.FieldsValue
    require("f18" in fields, "part manager name field is missing")
    manager_name = None if fields["f18"] is None else node_name(fields["f18"])
    directory = fields.get("f370")
    require(isinstance(directory, Mapping), "part manager requires its actual directory")
    rows = directory.get("items")
    require(isinstance(rows, (tuple, list)) and len(rows) == directory.get("n") == fields.get("f40c") == 1
            and isinstance(rows[0], Mapping), "part manager requires exactly one counted configuration")
    part = rows[0].get("o")
    require(isinstance(part, ArchiveNode) and part.ClassValue == CONFIGURATION
            and part.FieldsValue.get("f08") == 0, "part manager requires an ordinary local configuration")
    require(fields.get("f360") is part and fields.get("f368") is part,
            "part manager selectors must alias its actual configuration")
    values = part.FieldsValue
    return part, {
        "name": manager_name, "configuration": node_name(values.get("f18")),
        "comment": as_text(values.get("f4a8")), "alternate_name": as_text(values.get("f498")),
        "description": as_text(values.get("f1f8")), "local_id": values["f08"],
        "f658": fields["f658"], "updated_at": values["f678"],
    }


def read_body(context, reader, node):
    require((reader.NestingDepth == 1) == (node.ClassValue == MANAGER),
            "part manager has an unsupported root or nested manager")
    ReadBodyMut(context, reader, node)


def read_manager(data, version, grammar):
    context = context_for(version, grammar)
    reader = GraphReader(BinaryReader(data), ArchiveMaps(1), partial(read_body, context))
    root = ReadNodeMut(reader)
    part_owner(root)
    require(not reader.Cursor.GetRemaining(), "part manager has trailing bytes")
    require(not any(context.FlagsValue.values()), "part manager left an active context")
    context.UsageValue.IsComplete = True
    return root, reader.MapValue.Snapshot(), GetBodyReport(context.UsageValue)


def write_fields(frame, rules):
    for rule in rules:
        if rule.KindValue == "Context":
            context = frame.WriterValue.ContextValue
            context.UsageValue.FieldCalls["Context"] += 1
            ChangeFlagsMut(context, rule)
        elif rule.KindValue == "Virtual" and rule.ModeValue == "Flag":
            context = frame.WriterValue.ContextValue
            context.UsageValue.FieldCalls["Virtual"] += 1
            active = GetVirtualRule(context, frame.NodeValue, rule)
            require(type(active) is bool, "part manager virtual flag requires its concrete boolean")
            if active:
                frame.FieldsWriter(frame, rule.BodyValue)
        else:
            WriteFieldsMut(frame, (rule,))


def write_body(writer, node):
    require((writer.NestingDepth == 1) == (node.ClassValue == MANAGER),
            "part manager has an unsupported root or nested manager")
    name = CheckBodyMut(writer.ContextValue, node)
    frame = WriteFrame(writer, FieldScope(node.FieldsValue), node, WriteSchemaMut, write_fields)
    WriteSchemaMut(frame, name)


def emit_graph(root, version, grammar):
    context = context_for(version, grammar)
    writer = BodyWriter(ArchiveMaps(1), context, write_body)
    WriteNodeMut(writer, root)
    require(not any(context.FlagsValue.values()), "part manager left an active context")
    context.UsageValue.IsComplete = True
    return bytes(writer.OutputValue), GetBodyReport(context.UsageValue)


def write_manager(root, version, grammar):
    part_owner(root)
    return emit_graph(root, version, grammar)
