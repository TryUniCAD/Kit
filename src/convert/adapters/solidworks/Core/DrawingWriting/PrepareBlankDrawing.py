from pathlib import Path as FilePath
from uuid import UUID as UuidValue

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.DrawingWriting.BlankSelfFile import BlankSelfFile
from convert.adapters.solidworks.Core.DrawingWriting.BlankTargetName import (
    BlankTargetName,
)
from convert.adapters.solidworks.Core.DrawingWriting.MakeBlankWriteRecipe import (
    MakeBlankWriteRecipe,
)
from convert.adapters.solidworks.Core.DrawingWriting.NeedBlankDrawing import (
    NeedBlankDrawing,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.DrawingFile import (
    DrawingFile,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.MakeBlankFile import (
    MakeBlankFile,
)
from interchange.document.Models.DocumentModel import CadDocument


# complete drawing construction resolves only typed intent and the destination identity before the writer can publish a file
def PrepareBlankDrawing(
    DocumentValue: CadDocument,
    TargetValue: FilePath,
    WrittenAt: int,
    BlockValue: UuidValue,
    OptionsValue: WriteOptions,
) -> DrawingFile:
    _ = BlankTargetName(DocumentValue, TargetValue)
    Drawing = NeedBlankDrawing(DocumentValue)
    FileValue = BlankSelfFile(TargetValue, OptionsValue.values.get("final_destination"), WrittenAt)
    return MakeBlankFile(MakeBlankWriteRecipe(Drawing, FileValue, BlockValue))
