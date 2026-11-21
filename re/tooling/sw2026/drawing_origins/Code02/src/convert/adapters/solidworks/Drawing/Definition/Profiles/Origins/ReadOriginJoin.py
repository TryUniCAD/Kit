from ntpath import normcase as NormCase, normpath as NormPath

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrRows import ReadCmgrRows
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrText import ReadCmgrText
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.Origin.FindOriginNode import (
    FindOriginNode,
)
from convert.adapters.solidworks.Drawing.Construction.Indexes.ReadViewIndex import (
    ReadViewIndex,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileMap import (
    NeedProfileMap,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileNode import (
    NeedProfileNode,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.Origins.CheckOriginComponent import (
    CheckOriginComponent,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.Origins.OriginChild import (
    OriginChild,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.Origins.OriginProfile import (
    OriginProfile,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.ProfileDisplay import (
    ProfileDisplay,
)


def ReadOriginJoin(
    DisplayValue: ProfileDisplay, ChildValue: OriginChild
) -> OriginProfile:
    Reference = CheckOriginComponent(DisplayValue)
    IndexValue = ReadViewIndex(DisplayValue.ViewValue)
    if NormCase(NormPath(str(IndexValue.PathValue))) != NormCase(
        NormPath(str(ChildValue.PathValue))
    ):
        raise ValueError(
            "drawing origin resolver path differs from its actual view reference"
        )
    ManagerValue = ChildValue.ManagerValue.RootValue
    Configurations = ReadCmgrRows(ManagerValue)
    if (
        len(Configurations) != 1
        or ManagerValue.FieldsValue.get("f360") is not Configurations[0]
        or ManagerValue.FieldsValue.get("f368") is not Configurations[0]
    ):
        raise ValueError("drawing origin child has no unique active configuration")
    Configuration = NeedProfileNode(Configurations[0], "moPartConfiguration_c")
    NameValue = NeedProfileNode(Configuration.FieldsValue.get("f18"), "moNodeName_c")
    NameText = ReadCmgrText(NameValue.FieldsValue.get("f08"))
    SelfValue = NeedProfileNode(
        ChildValue.LinkValue.ConfigValue.HeaderValue.FieldsValue.get("f38"),
        "moExtObject_c",
    )
    SelfConfig = NeedProfileMap(SelfValue.FieldsValue.get("refcfg"))
    if (
        Reference.FieldsValue.get("f3c0") is None
        or IndexValue.ConfigName != NameText
        or IndexValue.ConfigId != FieldInt(Configuration.FieldsValue, "f08")
        or ReadCmgrText(SelfConfig.get("f08")) != NameText
        or FieldInt(SelfConfig, "f10") != IndexValue.ConfigId
    ):
        raise ValueError(
            "drawing origin configuration does not bind the actual child manager"
        )
    KeyValue = NeedProfileMap(DisplayValue.ReferenceValue.FieldsValue.get("ff0"))
    NativeId = FieldInt(KeyValue, "f00")
    CreatedAt = FieldInt(KeyValue, "f08")
    if NativeId <= 0:
        raise ValueError(
            "drawing origin requires a positive ordinary persistent feature id"
        )
    ProfileValue = FindOriginNode(ChildValue.LinkValue, NativeId)
    if CreatedAt != DatumTime(ChildValue.LinkValue.ConfigValue.HeaderValue, NativeId):
        raise ValueError("drawing origin feature creation epoch differs")
    SketchValue = NeedProfileNode(ProfileValue.FieldsValue.get("pd_f80"), "sgSketch")
    return OriginProfile(
        DisplayValue,
        ChildValue,
        Configuration,
        ProfileValue,
        SketchValue,
        NativeId,
        CreatedAt,
    )
