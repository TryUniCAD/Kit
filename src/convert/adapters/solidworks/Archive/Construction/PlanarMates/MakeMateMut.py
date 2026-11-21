from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTime import (
    FeatureTime,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.MakeModelFeat import (
    MakeModelFeat,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CheckMateCtx import (
    CheckMateCtx,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MakeDetached import (
    MakeDetached,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MakeEndpoint import (
    MakeEndpoint,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MakeResolved import (
    MakeResolved,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MateContext import (
    MateContext,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.PlanarMateIn import (
    PlanarMateIn,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadMateClass import (
    ReadMateClass,
)
from convert.adapters.solidworks.Archive.Construction.Perpendicular.CheckPerpEnds import (
    CheckPerpEnds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# ordinary mate graphs are synthesized from actual typed selections before their shared allocator and anchor state commit
def MakeMateMut(Context: MateContext, InputValue: PlanarMateIn) -> ArchiveNode:
    _ = CheckMateCtx(Context, InputValue)
    Endpoints = tuple(
        MakeEndpoint(Context.AssemblyValue, Value) for Value in InputValue.Selections
    )
    CheckPerpEnds(InputValue, Endpoints)
    Resolved = tuple(MakeResolved(Value) for Value in Endpoints)
    Detached = [
        {"k": Index, "o": MakeDetached(Value, Context)}
        for Index, Value in enumerate(Endpoints)
    ]
    ClassName = ReadMateClass(InputValue.KindValue)
    MateValue = MakeModelFeat(
        ClassName, InputValue.NameValue, Context.GroupValue, Context.TargetValue
    )
    Fields = MateValue.FieldsValue
    Fields.update(FeatureTime(InputValue.CreatedValue))
    Fields.update(
        dict.fromkeys(("f388", "f390", "f394", "f3b8", "has_f3c0", "f438", "f480"), 0)
    )
    Fields.update(dict.fromkeys(("f3c0", "f430", "f468", "f470", "f478"), None))
    Fields.update(
        {
            "f370": [],
            "f3b4": 0 if InputValue.KindValue == "perpendicular" else 1,
            "f3c8": Detached,
            "f410": [{"o": Value} for Value in Resolved],
            "f448": [],
            "f488": "",
            "f490": "",
        }
    )
    Counter = FieldInt(Context.AssemblyValue.FieldsValue, "fd48")
    MateId = Context.Allocator.AllocateMut(MateValue)
    for Index, Wrapper in enumerate(Resolved):
        Wrapper.FieldsValue.update(
            {"f74": MateId, "f78": Counter + Index, "f7c": Index}
        )
    Context.AssemblyValue.FieldsValue["fd48"] = Counter + 2
    InputValue.FixedValue.FieldsValue["f408"] = 1
    return MateValue
