from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylMateCtx import (
    CylMateCtx,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylMateIn import (
    CylMateIn,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTime import (
    FeatureTime,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import (
    InitFeatureMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# active wrappers register to their newly allocated mate while detached supports remain independent
def PutCylMateMut(
    Context: CylMateCtx,
    IntentValue: CylMateIn,
    Active: tuple[ArchiveNode, ...],
    Support: tuple[ArchiveNode, ...],
) -> ArchiveNode:
    StateValue = Context.StateValue
    Settings = Context.InputValue
    MateValue = ArchiveNode(RuntimeClass("moMateConcentric", 1), {})
    InitFeatureMut(
        MateValue, IntentValue.NameValue, StateValue.GroupValue, Settings.TargetValue
    )
    FieldsValue = MateValue.FieldsValue
    FieldsValue["f35c"] = 0
    FieldsValue.update(FeatureTime(Settings.HeaderValue.CreatedAt))
    FieldsValue.update(
        dict.fromkeys(("f388", "f390", "f394", "f3b8", "has_f3c0", "f438", "f480"), 0)
    )
    FieldsValue.update(dict.fromkeys(("f3c0", "f430", "f468", "f470", "f478")))
    FieldsValue.update(
        f370=[],
        f3b4=IntentValue.AlignmentCode,
        f3c8=[{"k": Index, "o": WrapValue} for Index, WrapValue in enumerate(Support)],
        f410=[{"o": WrapValue} for WrapValue in Active],
        f448=[],
        f488="",
        f490="",
        f4b8=int(IntentValue.RotationLocked),
        f4c4=-1,
    )
    MateId = StateValue.Allocator.AllocateMut(MateValue)
    Parent = StateValue.RootValue.FieldsValue
    Counter = FieldInt(Parent, "fd48")
    for Index, Wrapper in enumerate(Active):
        Wrapper.FieldsValue.update(f74=MateId, f78=Counter + Index, f7c=Index)
    Parent["fd48"] = Counter + len(Active)
    return MateValue
