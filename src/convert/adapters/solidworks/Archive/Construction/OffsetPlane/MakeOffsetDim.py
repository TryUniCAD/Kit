from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndInput import (
    BlindEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Blind.MakeBlindParam import (
    MakeBlindParam,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeDimValue import (
    MakeDimValue,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeHandleMut import (
    MakeHandleMut,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeExtrusionView import (
    MakeExtrudeView,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffsetInput import (
    OffsetInput,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# a reference plane keeps one real local distance handle tied to the plane before publication
def MakeOffsetDim(
    OwnerValue: ArchiveNode,
    InputValue: OffsetInput,
    Allocator: PersistentIds,
    DesignIntent: bool,
    SelectedLeader: int,
) -> DimensionGraph:
    Parameter = MakeBlindParam(
        BlindEndInput(InputValue.DistanceValue, False, InputValue.VersionValue), 1
    )
    Parameter.FieldsValue["owner"] = OwnerValue
    Dimension = MakeDimValue(OwnerValue, Parameter)
    _ = Allocator.AllocateMut(Dimension, "f50")
    Handle = MakeHandleMut(OwnerValue, Dimension)
    Display = MakeExtrudeView(OwnerValue, Handle, False, DesignIntent, SelectedLeader)
    return DimensionGraph(Parameter, Dimension, Handle, Display)
