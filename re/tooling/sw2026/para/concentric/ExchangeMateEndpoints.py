from hashlib import sha256
from pathlib import PureWindowsPath

from AssemblyMateDescriptor import typed_node
from ExchangeMessagePack import ExchangeMap

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadChildStamp, ReadFileKey, ReadFileText
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName, ReadRows, RequireRecord
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarChild
from convert.adapters.solidworks.Assembly.PlanarMates.ReadChain import ReadChain
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CheckCylCaps import CheckCylCaps
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CheckCylIds import CheckCylIds
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CheckCylSide import CheckCylSide
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CylChild import CylChild
from convert.adapters.solidworks.Core.TypedMates.Cylinders.PickCylFace import PickCylFace
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylAttr import ReadCylAttr
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylNodes import ReadCylNodes
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylOwner import ReadCylOwner
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylRef import ReadCylRef
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylWords import ReadCylWords
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyScalar import ReadBodyScalar
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


def selected_attribute(nodes, owner, name, index):
    return ReadBodyScalar(nodes, {name: ReadCylAttr(nodes, owner, name)}, name, index)


def child_exchange_face(payload):
    archive = SldprtArchive.from_bytes(payload)
    if archive.format_version != 4 or ContainerMo(archive.streams) != 19000:
        raise ValueError("exchange mate requires the measured current child archive format")
    link = ReadNativeLink(archive, 0)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000).RootValue.FieldsValue
    config = typed_node(manager.get("f360"), "moPartConfiguration_c")
    rows = ReadRows(RequireRecord(manager.get("f370")).get("items"))
    if len(rows) != 1 or rows[0].get("o") is not config or manager.get("f368") is not config:
        raise ValueError("exchange mate requires the actual ordinary child configuration")
    nodes = ReadCylNodes(archive)
    face, surface, body = PickCylFace(nodes)
    atom = selected_attribute(nodes, body, "ATOM_ID_2001", 1)
    feature, arc = ReadCylOwner(link, atom)
    child = CylChild(link, nodes, face, surface, feature, arc, atom, sha256(payload).hexdigest())
    CheckCylSide(child)
    return child, config


def project_exchange_target(root, component):
    assembly = typed_node(root, "moAssembly_c")
    occurrence = ReadChain(assembly, component)
    name = ReadNodeName(occurrence)
    root_name = ReadNodeName(assembly)
    ext_feature = typed_node(occurrence.FieldsValue.get("f4f8"), "moExtFeature_c")
    if (any(symbol in name or symbol in root_name for symbol in ("@", "\x00", "/", "\\"))
        or ReadFileText(ext_feature.FieldsValue.get("f38")) != name):
        raise ValueError("exchange target requires distinct actual direct occurrence and assembly labels")
    return occurrence, f"{name}@{root_name}"


def ordinary_uda_words(child):
    slots = tuple(ReadCylWords(child.NodesValue, child.FaceValue, index) for index in (2, 3))
    if tuple(map(len, slots)) != (5, 2):
        raise ValueError("exchange mate requires the actual ordinary lateral face integer slots")
    words = (0, 0, *slots[0], *slots[1])
    if any(not -(1 << 31) <= value < 1 << 31 for value in words):
        raise ValueError("exchange mate face words must fit native signed long")
    return words


def check_selected_face(child, component, file_key):
    fields = component.FieldsValue
    if fields.get("ff0") is not None:
        raise ValueError("exchange mate has an unqualified secondary selection")
    face = typed_node(fields.get("fe8"), "moFaceRef_c").FieldsValue
    rows = ReadRows(face.get("f10"))
    if not rows:
        raise ValueError("exchange mate requires an actual lateral face owner")
    side = typed_node(rows[0].get("f08"), "moFromSktEntSurfIdRep_c")
    ReadCylRef(side, child)
    tag = selected_attribute(child.NodesValue, child.FaceValue, "SWEntUnchanged", 0) >> 16 & 0xFFFF
    if not tag or FieldInt(face, "f70") != tag or FieldInt(side.FieldsValue, "f38") != child.ArcMarker:
        raise ValueError("exchange mate selection lost its actual lateral kernel face identity")
    CheckCylCaps(child, face)
    files = []
    for index in (0, 1, 3):
        reference = rows[index]["f08"]
        keeper = typed_node(RequireRecord(reference.FieldsValue.get("f10")).get("f10"), "moFR_c")
        files.append(typed_node(keeper.FieldsValue.get("f08"), "moExtObject_c"))
    if any(value is not files[0] for value in files) or ReadFileKey(files[0]) != file_key:
        raise ValueError("exchange mate side and caps target a different actual child keeper")
    return files[0]


def project_exchange_mate_endpoints(root, mate, child_payload, *, historical_keeper_locator=None):
    root = typed_node(root, "moAssembly_c")
    node = typed_node(mate, "moMateConcentric")
    CheckCylIds(node)
    mate_id = FieldInt(node.FieldsValue, "f08")
    if (not 0 < mate_id <= 0x7FFFFFFF or FieldInt(node.FieldsValue, "f3b4") not in (1, 2)
        or FieldInt(node.FieldsValue, "f4b8") not in (0, 1)):
        raise ValueError("exchange requires an ordinary live concentric mate")
    child, config = child_exchange_face(child_payload)
    child_header = child.LinkValue.ConfigValue.HeaderValue
    child_key = ReadFileKey(typed_node(child_header.FieldsValue.get("f38"), "moExtObject_c"))
    config_id = FieldInt(config.FieldsValue, "f08")
    config_name = ReadNodeName(config)
    basename = PureWindowsPath(child_key[1]).name.casefold()
    keeper_key = child_key
    if historical_keeper_locator is not None:
        path = PureWindowsPath(historical_keeper_locator)
        if not path.is_absolute() or path.name.casefold() != basename:
            raise ValueError("exchange mate requires an exact historical locator for the same child filename")
        keeper_key = (child_key[0], historical_keeper_locator, *child_key[2:])
    words = ordinary_uda_words(child)
    uda = "".join(f"{value} " for value in words)
    ends = []
    occurrences = set()
    targets = set()
    keepers = set()
    for index, row in enumerate(ReadRows(node.FieldsValue.get("f410"))):
        wrapper = typed_node(row.get("o"), "moCylinderRef_w")
        fields = wrapper.FieldsValue
        if (FieldInt(fields, "f74") != mate_id or FieldInt(fields, "f7c") != index
            or not 0 <= FieldInt(fields, "f78") < FieldInt(root.FieldsValue, "fd48")):
            raise ValueError("exchange mate requires the actual ordered active wrapper")
        component = typed_node(fields.get("f58"), "moCompFace_c")
        occurrence, target = project_exchange_target(root, component)
        ReadChildStamp(wrapper, occurrence, PlanarChild(child_header, {}), config_id, config_name, basename)
        keepers.add(id(check_selected_face(child, component, keeper_key)))
        occurrences.add(FieldInt(occurrence.FieldsValue, "f08"))
        targets.add(target)
        reference = ExchangeMap((("class", "moCompFace_c"), ("target", target), ("uda0", uda)))
        ends.append(ExchangeMap((("class", "moCylinderRef_w"), ("dummy", reference))))
    if len(occurrences) != 2 or len(targets) != 2 or mate_id in occurrences:
        raise ValueError("exchange mate requires two distinct selected occurrence owners")
    if len(keepers) != 1:
        raise ValueError("exchange mate endpoints do not share the actual child keeper")
    return tuple(ends)
