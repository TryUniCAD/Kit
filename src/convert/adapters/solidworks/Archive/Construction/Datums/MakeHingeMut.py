from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import (
    SetCfgStampMut,
)
from convert.adapters.solidworks.Archive.Construction.Datums.MakeHingePick import (
    MakeHingePick,
)
from convert.adapters.solidworks.Archive.Construction.Datums.PutHingeViews import (
    PutHingeViews,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import (
    KAtomLists,
    KAtomWords,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import (
    InitFeatureMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import (
    MakePartHeaders,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName


# a generated finite axis registers after the joined stock and retains both actual principal supports
def MakeHingeMut(
    SystemValue: PartSystem,
    Settings: PartBuildInput,
    Allocator: PersistentIds,
    NameValue: str,
    BoundsValue: tuple[tuple[float, float, float], tuple[float, float, float]],
) -> tuple[ArchiveNode, tuple[ArchiveNode, ArchiveNode, ArchiveNode]]:
    if (
        len(SystemValue.ConfigValues) != 1
        or SystemValue.ManagerValue.FieldsValue["f360"]
        is not SystemValue.ConfigValues[0]
    ):
        raise ValueError("local finite hinge requires one actual active configuration")
    if type(NameValue) is not str or not NameValue or "\x00" in NameValue:
        raise ValueError("finite hinge requires an actual feature name")
    if any(ReadNodeName(Value) == NameValue for Value in SystemValue.FeatureValues):
        raise ValueError("finite hinge requires a distinct authored feature name")
    StartValue, EndValue = PutHingeViews(SystemValue, BoundsValue)
    if not StartValue > 0.0 > EndValue:
        raise ValueError(
            "principal support must have an interior through origin interval"
        )
    Feature = ArchiveNode(RuntimeClass("moRefAxis_c", 1), {})
    InitFeatureMut(
        Feature, NameValue, SystemValue.RootValue, Settings.TargetValue, Allocator
    )
    Feature.FieldsValue.update(dict.fromkeys(KAtomWords, 0))
    Feature.FieldsValue.update({KeyValue: [] for KeyValue in KAtomLists})
    Feature.FieldsValue.update(
        f35c=0,
        f368={"n": 0, "items": []},
        f388={"n": 0, "items": []},
        f538=None,
        f4a0=1,
        f6c0=MakePoint(ZValue=StartValue),
        f6dc=4,
        f6e0=0,
        f6e8=None,
        f6f0=0,
    )
    SetCfgStampMut(SystemValue.ConfigValues[0], Allocator)
    Headers = MakePartHeaders(SystemValue, Settings, Allocator)
    FirstPick, SecondPick = (
        MakeHingePick(
            SystemValue,
            SystemValue.SystemValues.PlaneValues[AxisValue],
            AxisValue,
            Headers,
        )
        for AxisValue in ("y", "x")
    )
    Feature.FieldsValue["f700"] = ArchiveNode(
        RuntimeClass("moPlaneInterAxisData_c", 1),
        {
            "f18": MakePoint(ZValue=StartValue),
            "f30": MakePoint(ZValue=EndValue),
            "f08": StartValue,
            "f10": -EndValue,
            "f50": MakePoint(ZValue=-1.0),
            "f68": MakePoint(),
            "f80": FirstPick,
            "f88": SecondPick,
        },
    )
    return Feature, Headers
