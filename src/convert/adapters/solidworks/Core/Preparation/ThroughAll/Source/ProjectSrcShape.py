from convert.adapters.solidworks.Archive.Construction.BodyScope.SelectedStock import (
    SelectedStock,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.SourceRefs import (
    SourceRefs,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.ThruOwnerInput import (
    ThruOwnerInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughEndInput import (
    ThroughEndInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughPartSpec import (
    ThroughPartSpec,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.MakeSourceStock import (
    MakeSourceStock,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ReadSourceAxes import (
    ReadSourceAxes,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ReadSourceCirc import (
    ReadSourceCirc,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ReadSourceEnd import (
    ReadSourceEnd,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ReadSourceOps import (
    ReadSourceOps,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ReadSourceScale import (
    ReadSourceScale,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ReadSourceScope import (
    ReadSourceScope,
)
from interchange.document.Models.DocumentModel import CadDocument


# executable source geometry must preserve both semantic parents the centre point normal selections and explicit stock scope
def ProjectSrcShape(DocumentValue: CadDocument, OutputName: str) -> ThruOwnerInput:
    Owners = ReadSourceOps(DocumentValue)
    Stock, LinesValue = MakeSourceStock(DocumentValue, Owners, OutputName)
    Circle, CircleId, CenterId = ReadSourceCirc(
        DocumentValue, Owners.CutSketch, ReadSourceScale(DocumentValue)
    )
    ScopeId = ReadSourceScope(DocumentValue, Owners)
    AxesValue = ReadSourceAxes(DocumentValue, Owners)
    if {Value.id for Value in DocumentValue.selections} != {
        ScopeId,
        *(Value.SelectionId for Value in AxesValue),
    }:
        raise ValueError("source has unrepresented additional selections")
    CutEnd = ReadSourceEnd(Owners.CutValue)
    ShapeValue = ThroughPartSpec(
        Stock,
        Circle,
        Owners.CutSketch.name,
        Owners.CutValue.name,
        ThroughEndInput(
            "through_all_both" if CutEnd.second_end_condition else "through_all",
            CutEnd.reversed,
            19000,
        ),
    )
    RefsValue = SourceRefs(
        Owners.StockProfile.id,
        Owners.CutProfile.id,
        Owners.CutValue.id,
        Owners.CutSketch.id,
        CircleId,
        CenterId,
        ScopeId,
        Owners.StockValue.input_feature_ids,
        Owners.CutValue.input_feature_ids,
        str(Owners.StockValue.operation),
    )
    return ThruOwnerInput(
        ShapeValue,
        SelectedStock((Stock,), "selected", 19000),
        Owners.PlaneValues,
        LinesValue,
        AxesValue,
        RefsValue,
        str(DocumentValue.units),
    )
