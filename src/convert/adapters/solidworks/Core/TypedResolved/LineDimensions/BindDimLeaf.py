from convert.adapters.solidworks.Core.Native import NativeSketch
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismProf import (
    CheckPrismProf,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Checks.CheckBossState import (
    CheckBossState,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckLeafAtoms import (
    CheckLeafAtoms,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimLeafEnd import (
    CheckDimLeafEnd,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckLeafDims import (
    CheckLeafDims,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadRectLoop import (
    ReadRectLoop,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.BindReadLoop import (
    BindReadLoop,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# dimensioned cold leaves must own the actual sketch and its distinct forward boss depth
def BindDimLeaf(
    Sketch: NativeSketch, OwnerValue: ExtrudeOwner, LinkValue: NativeLink
) -> NativeSketch:
    Profile = OwnerValue.ProfileValue
    if OwnerValue.ParentsValue != (Profile,):
        raise ValueError(
            "dimensioned cold leaf requires one complete local boss profile"
        )
    CheckPrismProf(Profile)
    CheckBossState(OwnerValue.NodeValue)
    CheckLeafAtoms(OwnerValue.NodeValue, LinkValue.ConfigValue.RootValue)
    CheckDimLeafEnd(OwnerValue)
    Geometry = RequireNative(Profile.FieldsValue.get("pd_f80"), "sgSketch")
    LoopValue = ReadRectLoop(Geometry, LinkValue)
    DimsValue = LoopValue.DimsValue
    if DimsValue is None:
        raise ValueError("dimensioned cold leaf lacks its driving lengths")
    CheckLeafDims(OwnerValue, DimsValue)
    return BindReadLoop(Sketch, LoopValue)
