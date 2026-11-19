from pathlib import Path as FilePath
from time import time as ReadTime
from uuid import uuid4 as AllocateBlockId

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Container.Format import KDrawingFormatId
from convert.adapters.solidworks.Core.DrawingWriting.CheckBlankWriteOpts import (
    CheckBlankWriteOpts,
)
from convert.adapters.solidworks.Core.DrawingWriting.PrepareBlankDrawing import (
    PrepareBlankDrawing,
)
from interchange.document.Models.DocumentModel import CadDocument


# the registry can stage a complete generated blank drawing using its existing single file transaction
def EmitBlankDrawingMut(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult:
    Settings = CheckBlankWriteOpts(OptionsValue)
    if not isinstance(TargetValue, (str, FilePath)):
        raise TypeError("native blank drawing output requires a filesystem path")
    OutputPath = FilePath(TargetValue).expanduser().resolve()
    Payload = PrepareBlankDrawing(
        DocumentValue, OutputPath, int(ReadTime()), AllocateBlockId(), Settings
    ).BytesValue
    with OutputPath.open("wb" if Settings.overwrite else "xb") as OutputFile:
        if OutputFile.write(Payload) != len(Payload):
            raise OSError("short native drawing write")
    return WriteResult(
        OutputPath,
        KDrawingFormatId,
        len(Payload),
        application_usable=True,
        vendor_loadable=True,
    )
