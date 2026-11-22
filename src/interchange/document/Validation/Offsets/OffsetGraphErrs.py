from typing import Mapping as TypeMap

from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.Offsets.OffsetDefErrors import OffsetDefErrors
from interchange.document.Validation.Offsets.OffsetHistErrs import OffsetHistErrs
from interchange.document.Validation.Offsets.OffsetTopoErrs import OffsetTopoErrs
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.Offsets.FaceOffset import FaceOffset
from interchange.geometry.Models.Selection import Selection
from interchange.Records.RecordParameter import Parameter


# offset graph validation combines live operands history provenance and physical face ownership
def OffsetGraphErrs(
    Feature: FeatureStep,
    Document: CadDocument,
    Features: TypeMap[str, FeatureStep],
    IdentitySets: TypeMap[str, set[str]],
    Parameters: TypeMap[str, Parameter],
    Selections: TypeMap[str, Selection],
) -> tuple[str, ...]:
    if not isinstance(Feature.definition, FaceOffset):
        return ()
    return (
        *OffsetDefErrors(
            Feature, Feature.definition, IdentitySets, Parameters, Selections
        ),
        *OffsetHistErrs(Feature, Features),
        *OffsetTopoErrs(Feature, Document),
    )
