from pathlib import Path as FilePath
from uuid import UUID as UuidValue

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.DrawingWriting.BlankSelfFile import BlankSelfFile
from convert.adapters.solidworks.Core.DrawingWriting.BlankTargetName import (
    BlankTargetName,
)
from convert.adapters.solidworks.Core.DrawingWriting.MakeBlankWriteRecipe import (
    MakeBlankRecipe,
)
from convert.adapters.solidworks.Core.DrawingWriting.NeedBlankDrawing import (
    NeedBlankDraw,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.DrawingFile import (
    DrawingFile,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.MakeBlankFile import (
    MakeBlankFile,
)
from convert.adapters.solidworks.Core.DrawingWriting.Rewrite.PrepareRewrite import (
    PrepareRewrite,
)
from interchange.document.Models.DocumentModel import CadDocument


# complete drawing construction resolves only typed intent and the destination identity before the writer can publish a file
def BuildBlankDraw(
    DocumentValue: CadDocument,
    TargetValue: FilePath,
    WrittenAt: int,
    BlockValue: UuidValue,
    OptionsValue: WriteOptions,
) -> DrawingFile:
    if "solidworks.blank.profile" in DocumentValue.source.attributes:
        return PrepareRewrite(DocumentValue, TargetValue, WrittenAt, OptionsValue)
    _ = BlankTargetName(DocumentValue, TargetValue)
    Drawing = NeedBlankDraw(DocumentValue)
    FileValue = BlankSelfFile(
        TargetValue, OptionsValue.values.get("final_destination"), WrittenAt
    )
    return MakeBlankFile(MakeBlankRecipe(Drawing, FileValue, BlockValue))
