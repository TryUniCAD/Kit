from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# an angular constraint must bind an actual local datum through both original creation events
def ReadTiltRef(
    LinkValue: NativeLink,
    HeaderValue: ArchiveNode,
    Features: Mapping[int, ArchiveNode],
    WrapperValue: object,
    AxisValue: bool = False,
) -> tuple[ArchiveNode, ArchiveNode]:
    Wrapper = RequireNative(
        WrapperValue, "moLineRef_w" if AxisValue else "moPlaneRef_w"
    )
    WrapFields = Wrapper.FieldsValue
    RefValue = RequireNative(
        WrapFields.get("f58"), "moCompRefAxis_c" if AxisValue else "moCompRefPlane_c"
    )
    Fields = RefValue.FieldsValue
    Component = RequireNative(Fields.get("f58"), "moUnitComponent_c")
    ModelValue = LinkValue.ConfigValue.RootValue
    Identity = NativeRecord(Fields.get("ff0"))
    NativeId = Identity.get("f00")
    if (
        type(NativeId) is not int
        or WrapFields.get("f60") is not None
        or WrapFields.get("f68") != 1
        or WrapFields.get("has_f10") != 0
        or WrapFields.get("has_f18") != 0
        or Fields.get("ff8") is not None
        or Component is ModelValue.FieldsValue.get("f990")
        or Component.FieldsValue.get("owner") is not ModelValue
        or Component.FieldsValue.get("has_ext") != 0
    ):
        raise ValueError("angular datum requires its actual local selection")
    Target = RequireNative(
        Features.get(NativeId), "moRefAxis_c" if AxisValue else "moRefPlane_c"
    )
    CheckTreeAlias(LinkValue, (Wrapper, RefValue, Component, Target))
    if any(
        DatumTime(Header, NativeId) != Identity.get("f08")
        for Header in (LinkValue.ConfigValue.HeaderValue, HeaderValue)
    ):
        raise ValueError("angular datum selection contradicts its registered creation")
    return Target, Component
