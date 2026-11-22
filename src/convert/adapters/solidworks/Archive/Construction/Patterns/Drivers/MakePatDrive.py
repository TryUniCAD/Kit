from struct import pack as PackValue

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumPoint,
    KDatumVector,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.LinearStyle import (
    LinearStyle,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeCommonView import (
    MakeCommonView,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeDistTail import (
    MakeDistTail,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeHandleMut import (
    MakeHandleMut,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeValueFields import (
    MakeValueFields,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitNodeMut import (
    InitNodeMut,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PatAnnoValues import (
    PatAnnoValues,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PatDriveStyle import (
    PatDriveStyle,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.SetPatPointMut import (
    SetPatPointMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireRecord,
)


# each pattern parameter dimension handle and display keeps its own native owner and generated initial state
def MakePatDrive(
    OwnerValue: ArchiveNode,
    ModelValue: ArchiveNode,
    StyleValue: PatDriveStyle,
    DriveValue: int | float,
    DisplayId: int,
    IsCount: bool,
    Witnesses: tuple[KDatumVector, KDatumVector],
    LinearValue: LinearStyle,
) -> DimensionGraph:
    Parameter = ArchiveNode(
        RuntimeClass("moIntegerParameter_c" if IsCount else "moLengthParameter_c", 1),
        {},
    )
    InitNodeMut(Parameter, StyleValue.NameValue)
    Parameter.FieldsValue.update(
        owner=OwnerValue,
        f0c=0,
        f48=None,
        f58=DriveValue,
        **{"f60" if IsCount else "f68": 0},
    )
    Dimension = ArchiveNode(
        RuntimeClass("moNumberDim_c" if IsCount else "ParallelPlaneDistanceDim_c", 1),
        MakeValueFields(OwnerValue, Parameter),
    )
    Handle = MakeHandleMut(OwnerValue, Dimension)
    Fields = MakeCommonView(
        Handle, StyleValue.DesignIntent, StyleValue.SelectedLeader, 0 if IsCount else 18
    )
    Views = PatAnnoValues(ModelValue, StyleValue)
    Fields.update(owner=OwnerValue, f58=DisplayId, n2b0=len(Views), f2b0=Views)
    Fields["f6a0"] = {
        **RequireRecord(Fields["f6a0"]),
        "f38": DatumPoint(StyleValue.LabelValue),
    }
    Fields["f5b0"] = {
        **RequireRecord(Fields["f5b0"]),
        "data": PackValue("<d", DriveValue if DisplayId else 0.0),
    }
    if not IsCount:
        Fields.update(MakeDistTail())
        Fields.update(LinearValue.ProjectionValue)
        Fields["fb64"] = (FieldInt(Fields, "fb64") & ~0x103000) | LinearValue.FlagValue
        Fields["f8a4"] = (FieldInt(Fields, "f8a4") & ~0x50) | LinearValue.UnderText
    if StyleValue.NameValue == "D1":
        Fields["fad0"] = float(DriveValue)
    if StyleValue.NameValue == "D3":
        SetPatPointMut(Dimension, Fields, Witnesses)
    Display = ArchiveNode(
        RuntimeClass("moDisplayDim_c" if IsCount else "moDisplayDistanceDim_c", 1),
        Fields,
    )
    return DimensionGraph(Parameter, Dimension, Handle, Display)
