from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckThruCircle import (
    CheckThruCircle,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadThruStock import (
    ReadThruStock,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# both profiles must use their actual common part datum before the extra root layout can qualify
def CheckThruShape(
    LinkValue: NativeLink,
    Features: Mapping[int, ArchiveNode],
    StockValue: ExtrudeOwner,
    CutValue: ExtrudeOwner,
) -> None:
    RootValue = LinkValue.ConfigValue.RootValue
    StockFrame = ReadPrismFrame(
        StockValue.ProfileValue, RootValue, Features, FrontOnly=False
    )
    CutFrame = ReadPrismFrame(
        CutValue.ProfileValue, RootValue, Features, FrontOnly=False
    )
    if StockFrame != CutFrame:
        raise ValueError("through-all presentation profiles have different datums")
    Profiles = (StockValue.ProfileValue, CutValue.ProfileValue)
    Dependencies = tuple(
        RequireNative(Profile.FieldsValue.get(FieldName))
        for Profile in Profiles
        for FieldName in ("pd_f78", "pd_f80")
    )
    Components = tuple(
        RequireNative(Profile.FieldsValue.get("pd_f78")).FieldsValue.get("f58")
        for Profile in Profiles
    )
    CheckTreeAlias(
        LinkValue,
        (RootValue, *Dependencies, *(RequireNative(Value) for Value in Components)),
    )
    LoopValue = ReadThruStock(StockValue.ProfileValue, LinkValue)
    CheckThruCircle(CutValue.ProfileValue, LoopValue, LinkValue)
