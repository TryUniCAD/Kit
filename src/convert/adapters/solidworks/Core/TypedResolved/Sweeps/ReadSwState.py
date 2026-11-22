from dataclasses import dataclass as DataClass
from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.RequirePartPath import RequirePartPath
from convert.adapters.solidworks.Core.Preparation.Sweeps.SweepIntent import SweepIntent
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwGraph import (
    ReadSwGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.SwReadGraph import (
    SwReadGraph,
)
from interchange.geometry.Models.GeometryCurves import ArcGeometry, CircleGeometry


# generated cold bytes keep their own absolute source locator and constructor intent
@DataClass(frozen=True, slots=True)
class SwReadState(SwReadGraph):
    IntentValue: SweepIntent


# only the cold read path needs an output intent suitable for byte exact regeneration
def ReadSwState(Archive: SldprtArchive) -> SwReadState:
    GraphValue = ReadSwGraph(Archive)
    CircleValue, ArcValue = (
        GraphValue.SectionValue.CurveValue,
        GraphValue.PathValue.CurveValue,
    )
    HeaderValue = GraphValue.LinkValue.ConfigValue.HeaderValue.FieldsValue
    FileValue = GetFileRef(HeaderValue.get("f38")).PathValue
    EpochValue = HeaderValue.get("f70")
    if (
        type(CircleValue) is not CircleGeometry
        or type(ArcValue) is not ArcGeometry
        or type(EpochValue) is not int
    ):
        raise ValueError(
            "SOLIDWORKS cold sweep lacks its stored source identity or section geometry"
        )
    IntentValue = SweepIntent(
        PureWindowsPath(FileValue).stem,
        CircleValue,
        ArcValue,
        RequireScalar(GraphValue.DensityValue.FieldsValue.get("f58")),
        RequirePartPath(FileValue, EpochValue),
    )
    return SwReadState(
        GraphValue.LinkValue,
        GraphValue.FeatureValue,
        GraphValue.SectionValue,
        GraphValue.PathValue,
        GraphValue.DatumValues,
        GraphValue.ConfigValue,
        GraphValue.DensityValue,
        IntentValue,
    )
