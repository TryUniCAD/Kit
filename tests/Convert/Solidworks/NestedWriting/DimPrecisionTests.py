from dataclasses import replace as ReplaceValue

from pytest import raises as RaisesError

from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.PrepareNestedAssembly import (
    PrepNestedAsm,
)
from tests.Convert.Solidworks.NestedWriting.MakeDimNest import MakeDimNest
from tests.Convert.Solidworks.NestedWriting.MakeNestDoc import MakeNestDoc


# an authored millimetre number cannot borrow the archive word of a different driver
def TestExactDriver() -> None:
    WidthValue = 7.9338167953905945
    RoundTrip = (WidthValue * 0.001) / 0.001
    assert WidthValue != RoundTrip and WidthValue * 0.001 == RoundTrip * 0.001
    Locator = r"C:\KitNestedQueue\QueueFrame.SLDASM"
    _ = PrepNestedAsm(MakeDimNest(WidthOverride=RoundTrip), Locator, 1794011937)
    with RaisesError(
        ValueError, match="cannot preserve the authored millimetre driver"
    ):
        _ = PrepNestedAsm(MakeDimNest(WidthOverride=WidthValue), Locator, 1794011937)


# a physical placement word must invert to the actual authored translation
def TestExactOffset() -> None:
    DocumentValue = MakeNestDoc()
    GraphValue = DocumentValue.assembly
    assert GraphValue is not None
    FirstValue, *Remaining = GraphValue.instances
    MatrixValue = list(FirstValue.transform.values)
    MatrixValue[3] = 7.9338167953905945
    assert (MatrixValue[3] * 0.001) * 1000.0 != MatrixValue[3]
    Changed = ReplaceValue(
        FirstValue,
        transform=ReplaceValue(FirstValue.transform, values=tuple(MatrixValue)),
    )
    Portable = ReplaceValue(
        DocumentValue,
        assembly=ReplaceValue(GraphValue, instances=(Changed, *Remaining)),
    )
    with RaisesError(ValueError, match="cannot preserve the authored translation"):
        _ = PrepNestedAsm(Portable, r"C:\KitNestedQueue\QueueFrame.SLDASM", 1794011937)
