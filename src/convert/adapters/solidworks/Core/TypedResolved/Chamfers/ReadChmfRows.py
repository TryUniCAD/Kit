from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileText
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfOwners import (
    ChmfOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.Warm.CheckWarmSelf import (
    CheckWarmSelf,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative

# stock surface keys distinguish one cap selector or one actual permanent profile line
KChmfRoleKey = tuple[str, int | None, int | None]


# each selected reference row owns one actual stock surface representation
def EdgeChmfRows(Reference: ArchiveNode) -> tuple[ArchiveNode, ...]:
    return tuple(
        RequireNative(RowValue.get("f08"))
        for RowValue in NativeRows(Reference.FieldsValue.get("f10"))
    )


# a physical role can only be a numbered prior sketch line or a known signed stock cap
def ChmfRoleKey(Value: ArchiveNode) -> KChmfRoleKey:
    ClassName = Value.ClassValue.NameValue
    Ordinal = Value.FieldsValue.get("f38")
    Contour = Value.FieldsValue.get("f3c")
    if (
        type(Ordinal) is not int
        or Ordinal < 0
        or (Contour is not None and type(Contour) is not int)
    ):
        raise ValueError("chamfer has an unqualified stock face selector")
    if ClassName == "moEndFaceSurfIdRep_c" and Ordinal in (0, 1) and Contour == 0:
        return ClassName, Ordinal, Contour
    if ClassName == "moFromSktEntSurfIdRep_c" and Ordinal > 0 and Contour is None:
        return ClassName, Ordinal, None
    raise ValueError("chamfer has an unqualified stock face selector")


# historical file identity must resolve to the actual same local model and configuration
def CheckChmfFile(
    LinkValue: NativeLink,
    FileValue: ArchiveNode,
    TopHeader: ArchiveNode,
) -> None:
    HeaderValue = LinkValue.ConfigValue.HeaderValue
    ConfigSelf, TopSelf = (
        RequireNative(Header.FieldsValue.get("f38"), "moExtObject_c")
        for Header in (HeaderValue, TopHeader)
    )
    if FileValue in (ConfigSelf, TopSelf):
        raise ValueError("chamfer lacks the separate local historical file")
    ConfigValue = NativeRecord(ConfigSelf.FieldsValue.get("refcfg"))
    ConfigName = ConfigValue.get("f08")
    if not isinstance(ConfigName, CStringValue) or ConfigName.TextValue != "Default":
        raise ValueError("chamfer has an unsupported historical configuration")
    if NativeRecord(FileValue.FieldsValue.get("refcfg")) != {
        "f08": "Default",
        "f10": ConfigValue.get("f10"),
    }:
        raise ValueError("chamfer historical file targets a different configuration")
    for FieldName in ("h10", "h18"):
        NamesValue = tuple(
            ReadFileText(NativeRecord(Value.FieldsValue.get("shared"))[FieldName])
            for Value in (FileValue, ConfigSelf, TopSelf)
        )
        if not NamesValue[0] or len(set(NamesValue)) != 1:
            raise ValueError("chamfer historical file targets a different model")


# each surface must keep its own typed historical reference with both actual creation events
def ReadChmfRef(
    LinkValue: NativeLink,
    Value: ArchiveNode,
    OwnerValue: ArchiveNode,
    TopHeader: ArchiveNode,
    DirectValue: bool,
) -> ArchiveNode:
    OwnerFields = NativeRecord(Value.FieldsValue.get("f10"))
    Reference = RequireNative(OwnerFields.get("f10"), "moFR_c")
    Event = NativeRecord(Reference.FieldsValue.get("f10"))
    OwnerId = NativeNodeId(OwnerValue)
    Expected = DatumTime(LinkValue.ConfigValue.HeaderValue, OwnerId)
    if (
        OwnerFields.get("f08") is not (OwnerValue if DirectValue else None)
        or Expected == 2592000
        or DatumTime(TopHeader, OwnerId) != Expected
        or Event != {"f00": OwnerId, "f08": Expected}
    ):
        raise ValueError(
            "chamfer surface references a different producer or creation event"
        )
    CheckTreeAlias(LinkValue, (Value, Reference))
    return Reference


# the two selected graphs agree by ordered keys and remain separate from actual result keepers
def ReadChmfRows(
    LinkValue: NativeLink,
    Owners: ChmfOwners,
    TopHeader: ArchiveNode,
    *,
    IsSaved: bool = False,
) -> tuple[KChmfRoleKey, ...]:
    Selected, Detached = (
        EdgeChmfRows(Value) for Value in (Owners.SelectedRef, Owners.DetachedRef)
    )
    KeysValue = tuple(ChmfRoleKey(Value) for Value in Selected)
    Result = NativeRecord(
        NativeRecord(Owners.FeatureValue.FieldsValue.get("f880")).get("f18")
    )
    ResultValues = tuple(
        RequireNative(NativeRecord(RowValue.get("id")).get("f08"))
        for RowValue in NativeRows(Result.get("items"))
    )
    if (
        len(set((*Selected, *Detached, *ResultValues))) != 10
        or len(set(KeysValue)) != 4
        or KeysValue != tuple(ChmfRoleKey(Value) for Value in Detached)
        or Result.get("n") != 2
        or tuple(
            (Value.ClassValue.NameValue, Value.FieldsValue.get("f38"))
            for Value in ResultValues
        )
        != (("moSurfaceIdRep_c", None), ("moFilletSurfIdRep_c", 1))
    ):
        raise ValueError(
            "chamfer surface keeper has different ordered or result owners"
        )
    RefsValue = tuple(
        ReadChmfRef(LinkValue, Value, Owners.StockValue, TopHeader, False)
        for Value in (*Selected, *Detached)
    ) + tuple(
        ReadChmfRef(LinkValue, Value, Owners.FeatureValue, TopHeader, True)
        for Value in ResultValues
    )
    FileValue = RequireNative(RefsValue[0].FieldsValue.get("f08"), "moExtObject_c")
    if len(set(RefsValue)) != 10 or any(
        Value.FieldsValue.get("f08") is not FileValue for Value in RefsValue
    ):
        raise ValueError("chamfer surface references lack one actual local file owner")
    CheckTreeAlias(LinkValue, (FileValue,))
    if IsSaved:
        CheckWarmSelf(LinkValue, FileValue, TopHeader)
    else:
        CheckChmfFile(LinkValue, FileValue, TopHeader)
    return KeysValue
