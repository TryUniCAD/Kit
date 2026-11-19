from convert.adapters.solidworks.Core.DrawingWriting.Rewrite.ReadBlankValue import (
    ReadBlankValue,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.BlankDrawInput import (
    BlankDrawInput,
)


# native metadata must reach the existing official constructor contract before rewrite validation can begin
def ReadBlankInput(Value: object) -> BlankDrawInput:
    Result = ReadBlankValue(BlankDrawInput, Value)
    if type(Result) is not BlankDrawInput:
        raise TypeError(
            "blank metadata did not restore the complete official input type"
        )
    return Result
