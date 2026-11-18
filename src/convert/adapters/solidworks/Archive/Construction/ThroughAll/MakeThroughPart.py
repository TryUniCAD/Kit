from ntpath import basename as BaseName, splitext as SplitExt
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import (
    FinishBlindMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import (
    MakePartBaseMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.MakeThruProfile import (
    MakeThruProfile,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughPartSpec import (
    ThroughPartSpec,
)


# complete cold research parts reuse the ordinary root headers graph serializers and container with the authored depthless cut
def MakeThroughPart(
    InputValue: ThroughPartSpec, SettingsValue: PartBuildInput
) -> PartCandidate:
    if (
        type(InputValue) is not ThroughPartSpec
        or type(SettingsValue) is not PartBuildInput
    ):
        raise TypeError(
            "through all part requires typed neutral and explicit native settings"
        )
    PlanValue = InputValue.StockValue
    if (
        SplitExt(BaseName(SettingsValue.OutputValue.PathName))[0].casefold()
        != PlanValue.NameValue.casefold()
        or dict(SettingsValue.SystemValue.PlaneNames).get(PlanValue.AxisValue)
        != PlanValue.PlaneName
    ):
        raise ValueError(
            "through all file and principal support identities differ from the authored plan"
        )
    Allocator = PersistentIds()
    SystemValue = MakePartBaseMut(SettingsValue, PlanValue, Allocator)
    ProfileValue = MakeThruProfile(SystemValue, SettingsValue, PlanValue, Allocator)
    return FinishBlindMut(
        SystemValue,
        ProfileValue,
        SettingsValue,
        PlanValue,
        Allocator,
        ThroughValue=InputValue,
    )
