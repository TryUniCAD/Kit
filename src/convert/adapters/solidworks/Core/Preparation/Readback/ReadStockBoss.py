from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdBoss import (
    ReadColdBoss,
)
from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdOwners import (
    ReadColdOwners,
)
from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdSketch import (
    ReadColdSketch,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordParameter import Parameter


# each stock must keep its own typed depth and actual planar profile association
def ReadStockBoss(
    DocumentValue: CadDocument, Feature: FeatureStep, SketchValue: Sketch, Order: int
) -> tuple[FeatureStep, Parameter, Sketch, SupportPlane]:
    (DriverId,) = Feature.parameter_ids
    Driver = DocumentValue.parameter(DriverId)
    Owner, Plane = ReadColdOwners(DocumentValue, SketchValue, Driver)
    FeatureValue, ParameterValue = ReadColdBoss(Owner, Driver)
    Planar = ReadColdSketch(SketchValue)
    return (
        ReplaceValue(FeatureValue, order=Order),
        ParameterValue,
        ReplaceValue(
            Planar,
            constraints=tuple(
                ReplaceValue(Relation, provenance=None)
                for Relation in Planar.constraints
            ),
        ),
        ReplaceValue(Plane, attributes=FreezeMapping(), provenance=None),
    )
