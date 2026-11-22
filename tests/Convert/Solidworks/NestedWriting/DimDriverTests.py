from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.PrepareNestedAssembly import (
    PrepNestedAsm,
)
from tests.Convert.Solidworks.NestedWriting.CheckDriverEdit import CheckDriverEdit
from tests.Convert.Solidworks.NestedWriting.MakeDimNest import MakeDimNest


# a sketch scalar edit must fail preparation when its owned endpoint geometry is unchanged
def TestDimScalar() -> None:
    for IndexValue in range(2):
        DocumentValue = CheckDriverEdit(MakeDimNest(), IndexValue)
        try:
            _ = PrepNestedAsm(
                DocumentValue, r"C:\KitNestedQueue\QueueFrame.SLDASM", 1794011937
            )
        except ValueError as ErrorInfo:
            assert (
                "driving parameters disagree with their authored endpoint distances"
                in str(ErrorInfo)
            )
        else:
            raise AssertionError(
                "an authored scalar was silently replaced by its endpoint length"
            )
