from collections.abc import Mapping
from math import dist as Distance

from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import ReadVector
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRef import (
    CheckPrismRef,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatternDatum import (
    PatternDatum,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadPatTilt import (
    ReadPatTilt,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the line normal must agree with the actual selected archive datum and both owning logs
def ReadPatDatum(
    LinkValue: NativeLink,
    HeaderValue: ArchiveNode,
    Features: Mapping[int, ArchiveNode],
    PatternValue: ArchiveNode,
    HingeValue: ArchiveNode,
) -> PatternDatum:
    LineValue = RequireNative(PatternValue.FieldsValue.get("f1288"), "moLineRef_w")
    Reference = RequireNative(LineValue.FieldsValue.get("f58"), "moCompRefPlane_c")
    Component = RequireNative(Reference.FieldsValue.get("f58"), "moUnitComponent_c")
    Identity = NativeRecord(Reference.FieldsValue.get("ff0"))
    DatumId = Identity.get("f00")
    if type(DatumId) is not int:
        raise ValueError("pattern plane lacks a persistent datum identity")
    DatumValue = RequireNative(Features.get(DatumId), "moRefPlane_c")
    CheckPrismRef(Reference)
    CheckTreeAlias(LinkValue, (LineValue, Reference, Component, DatumValue))
    Reverse = PatternValue.FieldsValue.get("f1298")
    Fields = LineValue.FieldsValue
    if (
        Reference.FieldsValue.get("ff8") is not None
        or Component.FieldsValue.get("owner") is not LinkValue.ConfigValue.RootValue
        or Component is LinkValue.ConfigValue.RootValue.FieldsValue.get("f990")
        or Component.FieldsValue.get("has_ext") != 0
        or Fields.get("f60") is not None
        or any(
            Fields.get(NameValue) != 0 for NameValue in ("has_f10", "has_f18", "ff8")
        )
        or type(Reverse) is not int
        or Reverse not in (0, 1)
        or not all(
            DatumTime(Header, DatumId) == Identity.get("f08")
            for Header in (LinkValue.ConfigValue.HeaderValue, HeaderValue)
        )
    ):
        raise ValueError(
            "pattern direction does not bind its actual local datum and reversal"
        )
    Direction = ReadVector(Fields.get("fe0"))
    DatumKey = Reference.FieldsValue.get("f100")
    FrameValue, CenterValue, TiltValue = ReadPatTilt(
        LinkValue, HeaderValue, Features, DatumValue, HingeValue
    )
    if (
        DatumKey != 0
        or Fields.get("f68") != 1
        or Fields.get("fb0") != 0.0
        or abs(RequireScalar(Fields.get("fb8")) - 1.0) > 2e-15
        or Distance(ReadVector(Fields.get("fc8")), CenterValue) > 2e-15
        or Distance(Direction, FrameValue.NormalValue) > 2e-15
    ):
        raise ValueError(
            "pattern direction contradicts its angular plane border or signed normal"
        )
    return PatternDatum(DatumValue, LineValue, FrameValue, Reverse == 1, TiltValue)
