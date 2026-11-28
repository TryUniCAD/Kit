from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import (
    KAtomLists,
    KAtomWords,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import (
    InitFeatureMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.MakeOffsetData import (
    MakeOffsetData,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.MakeOffsetDim import (
    MakeOffsetDim,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.MakeOffsetRef import (
    MakeOffsetRef,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffsetFrame import (
    OffsetFrame,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffsetGraph import (
    OffsetGraph,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffsetInput import (
    OffsetInput,
)
from convert.adapters.solidworks.Archive.Construction.Origin.MakeOriginRef import (
    MakeOriginRef,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffBaseFrame import (
    OffBaseFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# an editable offset datum must allocate its driving distance before publishing the actual plane
def MakeOffsetMut(
    InputValue: OffsetInput,
    DatumValue: ArchiveNode,
    AxisValue: str,
    OwnerValue: ArchiveNode,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
    DesignIntent: bool,
    SelectedLeader: int,
) -> OffsetGraph:
    if (
        type(InputValue) is not OffsetInput
        or TargetValue.FileVersion != InputValue.VersionValue
    ):
        raise ValueError("offset construction requires its actual typed release input")
    RequireRootNode(OwnerValue, "moPart_c")
    Reference = MakeOriginRef(DatumValue, OwnerValue, AxisValue)
    BaseFrame = OffBaseFrame(AxisValue)
    LengthValue = InputValue.DistanceValue
    FrameValue = OffsetFrame(
        BaseFrame, -LengthValue if InputValue.IsReversed else LengthValue
    )
    NodeValue = ArchiveNode(RuntimeClass("moRefPlane_c", 1), {})
    InitFeatureMut(NodeValue, InputValue.NameValue, OwnerValue, TargetValue)
    DataValue = MakeOffsetData(
        FrameValue,
        MakeOffsetRef(Reference, DatumValue, BaseFrame),
        None,
        InputValue.IsReversed,
    )
    NodeValue.FieldsValue["f6f8"] = DataValue
    Distance = MakeOffsetDim(
        NodeValue, InputValue, Allocator, DesignIntent, SelectedLeader
    )
    DataValue.FieldsValue["f98"] = Distance.DisplayValue
    NodeValue.FieldsValue.update(dict.fromkeys(KAtomWords, 0))
    NodeValue.FieldsValue.update({FieldName: [] for FieldName in KAtomLists})
    NodeValue.FieldsValue.update(
        f35c=0,
        f368={"n": 0, "items": []},
        f388={"n": 0, "items": []},
        f538=None,
        f4a0=1,
        f6c0=MakePoint(),
        f6dc=4,
        f6e0=0,
        f6e8=None,
        f6f0=0,
    )
    _ = Allocator.AllocateMut(NodeValue)
    return OffsetGraph(NodeValue, DatumValue, FrameValue, Distance)
