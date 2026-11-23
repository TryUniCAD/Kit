from dataclasses import dataclass
from uuid import UUID

from AssemblyContentIndex import native_path
from AssemblyMateDescriptor import typed_node
from ConfigHeaderExchangeModel import MODEL_EXCHANGE_STREAM, project_active_config
from ExchangePack import OrderedMap, PackExchange
from PartObjectExchange import (
    DatumFields,
    ExchangeDocument,
    ObjectReference,
    SelectionFields,
)

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import (
    ReadRigidXform,
)
from convert.adapters.solidworks.Archive.Exchange.DatabaseClock import EncodeDbClock
from convert.adapters.solidworks.Archive.Exchange.WriteUnqlite import WriteUnqlite
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    RequireRecord,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

MANAGER = "moConfigurationMgr_c"
SELECTION = "moSelectionSetFolder_c"
PLANE = "moRefPlane_c"
MATES = "moMateGroup_c"
DOCUMENT = "uiAssemblyDoc_c"
MATE_STREAM = "Contents/Config-0-MatesList"


@dataclass(frozen=True, slots=True)
class ModelExchangeIds:
    manager: UUID
    selection: UUID
    planes: tuple[UUID, UUID, UUID]
    mates: UUID
    document: UUID
    plane_order: tuple[int, int, int] = (0, 1, 2)

    def __post_init__(self):
        identities = (
            self.manager,
            self.selection,
            *self.planes,
            self.mates,
            self.document,
        )
        if (
            len(set(identities)) != 7
            or len(identities) != 7
            or any(
                type(identity) is not UUID or identity.version != 4
                for identity in identities
            )
        ):
            raise ValueError(
                "model exchange requires seven distinct allocated record identities"
            )
        if tuple(sorted(self.plane_order)) != (0, 1, 2):
            raise ValueError(
                "model exchange requires one ordered reference to each standard datum"
            )


def model_owners(archive):
    link = ReadNativeLink(archive, 0)
    resolved = link.ResolvedValue
    root = typed_node(link.ConfigValue.RootValue, "moAssembly_c")
    header = ReadHeaderGraph(archive.require("Header2"), 19000)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000).RootValue
    mates = ReadMatesMut(archive.require(MATE_STREAM), resolved).RootsValue
    return root, header, manager, resolved.RootsValue, mates


def manager_record(manager, root, header):
    fields = typed_node(manager, MANAGER).FieldsValue
    if FieldInt(fields, "f08") != -1 or FieldInt(fields, "f28") != 0x40000000:
        raise ValueError("model exchange requires the ordinary configuration manager")
    title, locator = native_path(typed_node(header, "moHeader_c").FieldsValue["f38"], 3)
    if title != ReadNodeName(root):
        raise ValueError(
            "model exchange manager and header describe different assemblies"
        )
    description = (("description", locator),) if locator else ()
    return OrderedMap(
        (
            ("class", MANAGER),
            *description,
            ("hidden", False),
            ("id", FieldInt(fields, "f08")),
            ("overriddenReferenceIDs", ()),
            ("suppressed", False),
            ("updatestamp", FieldInt(fields, "f29c")),
        )
    )


def ordinary_feature(node, kind):
    fields = typed_node(node, kind).FieldsValue
    flags = (0x40000000, 0xC0000000) if kind == PLANE else (0x40000000,)
    if FieldInt(fields, "f28") not in flags or FieldInt(fields, "f08") <= 0:
        raise ValueError("model exchange requires an ordinary resolved " + kind)
    return ReadNodeName(node), FieldInt(fields, "f08"), FieldInt(fields, "f29c")


def selection_record(folder):
    name, identity, stamp = ordinary_feature(folder, SELECTION)
    items = RequireRecord(folder.FieldsValue["f3c0"])
    if FieldInt(items, "n") or items.get("items"):
        raise ValueError(
            "ordinary model exchange only covers an empty selection folder"
        )
    return SelectionFields(name, identity, stamp)


def datum_record(plane):
    name, identity, stamp = ordinary_feature(plane, PLANE)
    if FieldInt(plane.FieldsValue, "f6dc") != 5:
        raise ValueError(
            "ordinary model exchange requires the hidden standard datum mode"
        )
    definition = typed_node(
        plane.FieldsValue.get("f6f8"), "moDefaultRefPlnData_c"
    ).FieldsValue
    basis, offset = ReadRigidXform(RequireRecord(definition["f20"]))
    normal, point = (
        tuple(RequireScalar(RequireRecord(definition[key]).get(axis)) for axis in "xyz")
        for key in ("normal", "root")
    )
    if (
        point != (0.0, 0.0, 0.0)
        or offset != point
        or normal not in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    ):
        raise ValueError(
            "ordinary model exchange requires an unshifted principal plane"
        )
    return DatumFields(name, identity, stamp, normal, point, basis, offset)


def mate_group_record(group, mate_records):
    name, _, stamp = ordinary_feature(group, MATES)
    members = tuple((f"Mate{index}", mate) for index, mate in enumerate(mate_records))
    count = (("NumberMates", len(members)),) if members else ()
    return OrderedMap(
        (
            *members,
            *count,
            ("class", MATES),
            ("class", "moNodeList_c"),
            ("hidden", 0),
            ("name", name),
            ("suppressed", 0),
            ("updatestamp", stamp),
        )
    )


def model_toc(manager, identities):
    configuration = project_active_config(manager)
    selection = OrderedMap(
        (("class", SELECTION), ObjectReference(identities.selection))
    )
    mates = OrderedMap((("class", MATES), ObjectReference(identities.mates)))
    planes = OrderedMap(
        (
            ("class", PLANE),
            *(
                ObjectReference(identities.planes[index])
                for index in identities.plane_order
            ),
        )
    )
    model = OrderedMap(
        (
            ("class", "moAssembly_c"),
            ("configid", FieldInt(configuration.FieldsValue, "f08")),
            ("configname", ReadNodeName(configuration)),
            ("object", selection),
            ("object", mates),
            ("object", planes),
        )
    )
    return OrderedMap((("class", "object-map"), ("model", model)))


def standard_records(owners, identities):
    root, header, manager, resolved, _ = owners
    (folder,) = (node for node in resolved if node.ClassValue.NameValue == SELECTION)
    planes = tuple(node for node in resolved if node.ClassValue.NameValue == PLANE)
    if (
        len(planes) != 3
        or len({FieldInt(node.FieldsValue, "f08") for node in planes}) != 3
    ):
        raise ValueError(
            "ordinary model exchange needs three distinct resolved principal planes"
        )
    pairs = (
        (identities.manager, manager_record(manager, root, header)),
        (identities.selection, selection_record(folder)),
        *(
            (key, datum_record(plane))
            for key, plane in zip(identities.planes, planes, strict=True)
        ),
        (None, model_toc(manager, identities)),
        (identities.document, ExchangeDocument(DOCUMENT)),
    )
    return tuple(
        (b"TOC" if key is None else str(key).encode("ascii"), PackExchange(value))
        for key, value in pairs
    )


def model_records(owners, identities, mate_records):
    _, _, _, resolved, mates = owners
    if len(mates) != len(mate_records):
        raise ValueError("model exchange needs a record for every actual native mate")
    (group,) = (node for node in resolved if node.ClassValue.NameValue == MATES)
    *features, toc, document = standard_records(owners, identities)
    group_key = str(identities.mates).encode("ascii")
    group_value = PackExchange(mate_group_record(group, mate_records))
    return (*features, (group_key, group_value), toc, document)


def add_model_exchange(streams, owners, identities, created, mate_records):
    if MODEL_EXCHANGE_STREAM in streams:
        raise ValueError("assembly model exchange already has an owner")
    records = model_records(owners, identities, mate_records)
    data = WriteUnqlite(EncodeDbClock(created), records)
    return streams | {MODEL_EXCHANGE_STREAM: data}
