from dataclasses import replace as ReplaceValue

from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.AssemblyWriting.QualifyAsm import QualifyAsm
from interchange.document.Models.DocumentModel import CadDocument


# internal mate proof cannot qualify a changed public presentation recipe before its exact registry output passes native measurement
def QualifyPerpAsm(DocumentValue: CadDocument, ResultValue: WriteResult) -> WriteResult:
    GraphValue = DocumentValue.assembly
    if GraphValue is not None and any(
        str(Value.kind) == "perpendicular" for Value in GraphValue.mates
    ):
        return ReplaceValue(
            ResultValue,
            application_usable=False,
            vendor_loadable=False,
            metadata={
                **ResultValue.metadata,
                "native_qualification": "unmeasured_perpendicular_registry_profile",
            },
        )
    return QualifyAsm(ResultValue)
