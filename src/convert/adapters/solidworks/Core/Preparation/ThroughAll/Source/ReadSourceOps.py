from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ReadSourceDepth import (
    ReadSourceDepth,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ReadSourceEnd import (
    ReadSourceEnd,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ReadSourcePlane import (
    ReadSourcePlane,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.SourceOps import (
    SourceOps,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureExtrude import ExtrudeFeature


# stock join and both real profile parents must survive source projection before any new native owner is allocated
def ReadSourceOps(DocumentValue: CadDocument) -> SourceOps:
    Operations = tuple(
        Value
        for Value in DocumentValue.feature_timeline
        if type(Value.definition) is ExtrudeFeature
    )
    if len(Operations) != 2 or tuple(Value.operation for Value in Operations) != (
        "join",
        "cut",
    ):
        raise ValueError("source requires its actual stock join followed by one cut")
    Stock, CutValue = Operations
    Sketches = {Value.id: Value for Value in DocumentValue.sketches}
    if (
        len(Sketches) != 2
        or Stock.sketch_id not in Sketches
        or CutValue.sketch_id not in Sketches
    ):
        raise ValueError("source lacks its distinct actual stock and cut sketches")
    StockSketch, CutSketch = Sketches[Stock.sketch_id], Sketches[CutValue.sketch_id]
    Profiles = {
        Value.sketch_id: Value
        for Value in DocumentValue.feature_timeline
        if Value not in Operations and Value.sketch_id in Sketches
    }
    if len(Profiles) != 2 or StockSketch.support_plane_id != CutSketch.support_plane_id:
        raise ValueError(
            "source profiles have ambiguous ownership or different supports"
        )
    StockProfile, CutProfile = Profiles[StockSketch.id], Profiles[CutSketch.id]
    if Stock.input_feature_ids != (StockProfile.id,) or CutValue.input_feature_ids != (
        Stock.id,
        CutProfile.id,
    ):
        raise ValueError(
            "source operation dropped or changed its real profile and producer parents"
        )
    StockEnd, CutEnd = ReadSourceEnd(Stock), ReadSourceEnd(CutValue)
    if (
        StockEnd.end_condition != "mid_plane"
        or not StockEnd.symmetric
        or StockEnd.reversed
        or StockEnd.second_end_condition is not None
        or StockEnd.second_length is not None
    ):
        raise ValueError("source stock is outside the actual forward mid-plane profile")
    if (
        CutEnd.end_condition != "through_all"
        or CutEnd.length is not None
        or CutEnd.second_length is not None
        or CutEnd.second_end_condition not in (None, "through_all")
        or CutEnd.symmetric
        or CutValue.parameter_ids
    ):
        raise ValueError("source cut has unrepresented termination or dimension owners")
    return SourceOps(
        Stock,
        CutValue,
        StockSketch,
        CutSketch,
        StockProfile,
        CutProfile,
        ReadSourceDepth(DocumentValue, Stock),
        ReadSourcePlane(DocumentValue),
    )
