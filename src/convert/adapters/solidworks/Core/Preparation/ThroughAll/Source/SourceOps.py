from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.SourcePlane import (
    SourcePlane,
)
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Sketch import Sketch
from interchange.Records.RecordParameter import Parameter


# source projection must retain actual typed owners together before creating any reduced construction input
@DataClass(frozen=True, slots=True)
class SourceOps:
    StockValue: FeatureStep
    CutValue: FeatureStep
    StockSketch: Sketch
    CutSketch: Sketch
    StockProfile: FeatureStep
    CutProfile: FeatureStep
    DriverValue: Parameter
    PlaneValues: tuple[SourcePlane, ...]
