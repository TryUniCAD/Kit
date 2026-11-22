from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.solidworks.Core.Preparation.Circle.IsCircRead import IsCircRead
from convert.adapters.solidworks.Core.Preparation.Circle.PlanCircle import PlanCircle
from convert.adapters.solidworks.Core.Preparation.Circle.ReadCircInput import (
    ReadCircInput,
)
from convert.adapters.solidworks.Core.Writing.IsPartTarget import IsPartTarget
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.GeometryCurves import CircleGeometry


# only an authored single circle can enter this candidate path ahead of generic part emission
def HasCircWrite(DocumentValue: CadDocument) -> bool:
    return (
        DocumentValue.brep is None
        and len(DocumentValue.sketches) == 1
        and len(DocumentValue.feature_timeline) == 1
        and isinstance(DocumentValue.feature_timeline[0].definition, ExtrudeFeature)
        and len(DocumentValue.sketches[0].entities) == 1
        and isinstance(DocumentValue.sketches[0].entities[0].geometry, CircleGeometry)
    )


# selection proves the typed circle and signed support before any registry target is staged
def CanWriteCircle(DocumentValue: CadDocument, TargetValue: KTargetType) -> bool:
    ReadbackValue = IsCircRead(DocumentValue)
    if not ReadbackValue and not HasCircWrite(DocumentValue):
        return False
    try:
        InputValue = DocumentValue
        if ReadbackValue:
            NameValue = (
                PureWindowsPath(TargetValue).stem
                if isinstance(TargetValue, (str, FilePath))
                else DocumentValue.sketches[0].name
            )
            InputValue = ReadCircInput(DocumentValue, NameValue)
        PlanValue = PlanCircle(InputValue, Measured=True)
    except (IndexError, KeyError, TypeError, ValueError):
        return False
    return IsPartTarget(PlanValue.NameValue, TargetValue)
