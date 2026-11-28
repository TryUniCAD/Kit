from pathlib import Path as FilePath

from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
from convert.adapters.solidworks.Core.Preparation.Readback.ColdReadInput import (
    ColdReadInput,
)
from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from interchange.document.Models.DocumentModel import CadDocument


# the ordinary extrusion selector retains the same names for authored and regenerated readback
def PlainPartName(DocumentValue: CadDocument, PathValue: FilePath | None) -> str:
    if IsColdRead(DocumentValue):
        NameValue = (
            PathValue.stem if PathValue is not None else DocumentValue.sketches[0].name
        )
        DocumentValue = ColdReadInput(DocumentValue, NameValue)
    return PlanPartWrite(DocumentValue).NameValue
