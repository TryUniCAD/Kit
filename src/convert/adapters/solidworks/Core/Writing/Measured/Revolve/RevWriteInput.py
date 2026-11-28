from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Preparation.Revolve.Readback.ReadRevInput import (
    ReadRevInput,
)
from interchange.document.Models.DocumentModel import CadDocument


# the actual destination basename and typed readback owners determine the neutral projection
def RevWriteInput(DocumentValue: CadDocument, TargetValue: KTargetType, Settings: WriteOptions) -> CadDocument:
    if isinstance(TargetValue, (str, FilePath)):
        NameValue = FilePath(TargetValue).stem
    else:
        FinalValue = Settings.values.get("final_destination")
        if type(FinalValue) is not str:
            raise ValueError("measured revolve stream requires its exact inspected self locator")
        NameValue = PureWindowsPath(FinalValue).stem
    return ReadRevInput(DocumentValue, NameValue)
