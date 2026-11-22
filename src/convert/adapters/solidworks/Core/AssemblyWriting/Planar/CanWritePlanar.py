from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.solidworks.Container.Format import KAsmSuffix
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import (
    ReadAsmModel,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmOrder import (
    ReadAsmOrder,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Readback.IsPlanarRead import (
    IsPlanarRead,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Readback.PlanarReadIn import (
    PlanarReadIn,
)
from interchange.assembly.AssemblyEnums import MateKind
from interchange.document.Models.DocumentModel import CadDocument


# registry selection requires an owned direct part and the documented mate pair
def CanWritePlanar(Document: CadDocument, TargetValue: KTargetType) -> bool:
    GraphValue = Document.assembly
    if GraphValue is None or not isinstance(TargetValue, (str, FilePath)):
        return False
    OutputPath = FilePath(TargetValue).expanduser()
    if OutputPath.suffix.casefold() != KAsmSuffix or OutputPath.is_symlink():
        return False
    try:
        if tuple(
            Value.kind for Value in sorted(GraphValue.mates, key=ReadAsmOrder)
        ) != (MateKind.COINCIDENT, MateKind.DISTANCE):
            return False
        RootValue = ReadAsmModel(PlanarReadIn(Document) if IsPlanarRead(Document) else Document)
    except (KeyError, TypeError, ValueError):
        return False
    return OutputPath.stem == RootValue.RootValue.name
