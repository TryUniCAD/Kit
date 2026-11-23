from Core import Obj

from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.ReadOccName import ReadOccName
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import ReadStyleText
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileText
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt, ReadNodeName, ReadRows, RequireNode, RequireRecord,
)
from convert.adapters.solidworks.Assembly.PlanarMates.ReadChain import ReadChain


MATE_KINDS = {
    "moMateCoincident": (0, "moPlaneRef_w", "moCompRefPlane_c"),
    "moMateConcentric": (1, "moCylinderRef_w", "moCompFace_c"),
    "moMateDistanceDim_c": (5, "moPlaneRef_w", "moCompRefPlane_c"),
}


def typed_node(value, kind):
    node = RequireNode(value, kind)
    if node.ClassValue != RuntimeClass(kind, 1):
        raise ValueError("assembly mate descriptor uses an unsupported object schema")
    return node


def config_name(config, root):
    fields = typed_node(config, "moConfiguration_c").FieldsValue
    owner = fields.get("owner")
    configuration_id = FieldInt(fields, "f08")
    object_list = fields.get("f4e0")
    if (owner is not None and owner is not root
        or configuration_id < 0
        or any(ReadRows(fields.get(key)) for key in ("f420", "f430", "f460"))
        or object_list is not None
        and (FieldInt(RequireRecord(object_list), "n") != 0
             or ReadRows(RequireRecord(object_list).get("items")))):
        raise ValueError("assembly mate descriptor requires an ordinary configuration without overrides")
    return ReadStyleText(ReadNodeName(config), "assembly mate display configuration")


def display_occurrence(root, wrapper, wrapper_kind, component_kind, mate_id, order):
    fields = typed_node(wrapper, wrapper_kind).FieldsValue
    allocation = FieldInt(fields, "f78")
    if (FieldInt(fields, "f74") != mate_id or FieldInt(fields, "f7c") != order
        or not 0 <= allocation < FieldInt(root.FieldsValue, "fd48")):
        raise ValueError("assembly mate descriptor requires the actual ordered active wrapper allocation")
    target = typed_node(fields.get("f58"), component_kind)
    occurrence = ReadChain(root, target)
    external = typed_node(occurrence.FieldsValue.get("f4f8"), "moExtFeature_c")
    name = ReadStyleText(ReadNodeName(occurrence), "assembly mate display occurrence")
    if ReadFileText(external.FieldsValue.get("f38")) != name or "/" in name or "@" in name:
        raise ValueError("assembly mate descriptor has a conflicting direct occurrence name")
    base, number = ReadOccName(name)
    return occurrence, allocation, f"{base}<{number}>"


def make_mate_descriptor(root, active_config, mate):
    typed_node(root, "moAssembly_c")
    class_name = mate.ClassValue.NameValue if isinstance(mate, ArchiveNode) and isinstance(mate.ClassValue, RuntimeClass) else ""
    if class_name not in MATE_KINDS:
        raise ValueError("assembly mate descriptor has an unclassified concrete mate type")
    fields = typed_node(mate, class_name).FieldsValue
    mate_type, wrapper_kind, component_kind = MATE_KINDS[class_name]
    mate_id = FieldInt(fields, "f08")
    group = fields.get("owner")
    endpoints = ReadRows(fields.get("f410"))
    if (not 0 < mate_id <= 0x7FFFFFFF or len(endpoints) != 2 or FieldInt(fields, "f3b4") not in (1, 2)
        or any(FieldInt(fields, key) != 0 for key in ("f35c", "f388", "f390", "f394"))
        or group is not None and typed_node(group, "moMateGroup_c").FieldsValue.get("owner") is not root):
        raise ValueError("assembly mate descriptor requires one ordinary active two-end mate")
    first, second = (display_occurrence(root, row.get("o"), wrapper_kind, component_kind, mate_id, index)
                     for index, row in enumerate(endpoints))
    if (first[0] is second[0] or first[1] == second[1] or first[2] == second[2]
        or mate_id in {FieldInt(row[0].FieldsValue, "f08") for row in (first, second)}):
        raise ValueError("assembly mate descriptor needs distinct actual endpoint owners")
    name = ReadStyleText(ReadNodeName(mate), "assembly mate display name")
    return Obj("moBCMate_c", {
        "f08": config_name(active_config, root), "f10": 0, "f18": name,
        "f20": 2, "f24": mate_type, "f28": class_name,
        "f30": f"{name} ({first[2]},{second[2]})", "f38": 0, "f3c": mate_id,
    })
