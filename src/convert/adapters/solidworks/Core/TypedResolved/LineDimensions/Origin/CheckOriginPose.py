from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import (
    FrameXform,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the independent model origin coincides with zero local coordinates on either admitted principal support
def CheckOriginPose(
    ProfileValue: ArchiveNode, OriginValue: ArchiveNode, ModelValue: ArchiveNode
) -> None:
    FrameValue = NativeRecord(ProfileValue.FieldsValue.get("pd_ff0"))
    OriginFrame = NativeRecord(OriginValue.FieldsValue.get("pd_ff0"))
    SupportValue = RequireNative(
        ProfileValue.FieldsValue.get("pd_f78"), "moCompRefPlane_c"
    )
    Component = RequireNative(SupportValue.FieldsValue.get("f58"), "moUnitComponent_c")
    AxisCode = SupportValue.FieldsValue.get("f100")
    if (
        AxisCode not in (2, 3)
        or OriginFrame != FrameXform(PrincipalFrame("z"))
        or FrameValue != FrameXform(PrincipalFrame("y" if AxisCode == 2 else "z"))
        or Component.FieldsValue.get("owner") is not ModelValue
        or Component.FieldsValue.get("has_ext") != 0
    ):
        raise ValueError(
            "typed origin relation requires its canonical Front or Top support"
        )
