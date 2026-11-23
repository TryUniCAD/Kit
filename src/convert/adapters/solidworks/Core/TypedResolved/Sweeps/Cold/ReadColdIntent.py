from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.Preparation.RequirePartPath import RequirePartPath
from convert.adapters.solidworks.Core.Preparation.Sweeps.SweepIntent import SweepIntent
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.SwReadGraph import (
    SwReadGraph,
)
from interchange.geometry.Models.GeometryCurves import ArcGeometry, CircleGeometry


# the only construction inputs come from independently linked sweep owners and its typed self record
def ReadColdIntent(StateValue: SwReadGraph) -> SweepIntent:
    HeaderValue = StateValue.LinkValue.ConfigValue.HeaderValue.FieldsValue
    FileValue = GetFileRef(HeaderValue.get("f38"))
    EpochValue = HeaderValue.get("f70")
    SectionValue = StateValue.SectionValue.CurveValue
    PathValue = StateValue.PathValue.CurveValue
    if (
        type(EpochValue) is not int
        or type(SectionValue) is not CircleGeometry
        or type(PathValue) is not ArcGeometry
    ):
        raise ValueError(
            "cold SOLIDWORKS sweep lacks its exact curves or creation time"
        )
    return SweepIntent(
        FileValue.NameValue,
        SectionValue,
        PathValue,
        RequireScalar(StateValue.DensityValue.FieldsValue.get("f58")),
        RequirePartPath(FileValue.PathValue, EpochValue),
    )
