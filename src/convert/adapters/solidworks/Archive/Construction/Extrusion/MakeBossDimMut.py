from convert.adapters.solidworks.Archive.Construction.Blind.EndInput import KEndInput
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
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeAngleValue import (
    MakeAngleValue,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeBossView import (
    MakeBossView,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# every constructed feature dimension consumes its own real persistent identifier including the conditionally omitted from offset dimension
def MakeBossDimMut(
    OwnerValue: ArchiveNode,
    InputValue: KEndInput,
    OrdinalValue: int,
    DesignIntent: bool,
    SelectedLeader: int,
    Allocator: PersistentIds,
) -> DimensionGraph:
    RequireRootNode(OwnerValue, "moExtrusion_c")
    Parameter = MakeBlindParam(InputValue, OrdinalValue)
    Parameter.FieldsValue["owner"] = OwnerValue
    IsAngular = OrdinalValue in (3, 4)
    Dimension = (
        MakeAngleValue(OwnerValue, Parameter)
        if IsAngular
        else MakeDimValue(OwnerValue, Parameter)
    )
    _ = Allocator.AllocateMut(Dimension, "f50")
    HandleValue = MakeHandleMut(OwnerValue, Dimension)
    DisplayValue = MakeBossView(
        OwnerValue, HandleValue, IsAngular, DesignIntent, SelectedLeader
    )
    return DimensionGraph(Parameter, Dimension, HandleValue, DisplayValue)
