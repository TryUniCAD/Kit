from dataclasses import replace
from pathlib import Path as FilePath

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.DrawingWriting.BlankSelfFile import BlankSelfFile
from convert.adapters.solidworks.Core.DrawingWriting.Rewrite.NeedRewrite import (
    NeedRewrite,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.DrawingFile import (
    DrawingFile,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.MakeBlankFile import (
    MakeBlankFile,
)
from interchange.document.Models.DocumentModel import CadDocument


# public rewrite must preserve source owners while applying only the explicit destination and save event
def PrepareRewrite(
    DocumentValue: CadDocument,
    TargetValue: FilePath,
    WrittenAt: int,
    OptionsValue: WriteOptions,
) -> DrawingFile:
    InputValue = NeedRewrite(DocumentValue, TargetValue)
    FileValue = BlankSelfFile(
        TargetValue, OptionsValue.values.get("final_destination"), WrittenAt
    )
    return MakeBlankFile(replace(InputValue, FileValue=FileValue))
