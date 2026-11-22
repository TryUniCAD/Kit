from io import BytesIO

from convert import open_document as OpenDocument
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.PrepareNestedAssembly import (
    PrepNestedAsm,
)
from tests.Convert.Solidworks.NestedWriting.CheckDriverEdit import CheckDriverEdit
from tests.Convert.Solidworks.NestedWriting.MakeDimNest import MakeDimNest


# a compatible adjacent scalar edit needs different native evidence and retains the exact selected word
def TestDimScalar() -> None:
    Locator = r"C:\KitNestedQueue\QueueFrame.SLDASM"
    Baseline = PrepNestedAsm(MakeDimNest(), Locator, 1794011937)[0][1].BytesValue
    for IndexValue in range(2):
        DocumentValue = CheckDriverEdit(MakeDimNest(), IndexValue)
        GraphValue = DocumentValue.assembly
        assert GraphValue is not None
        Edited = GraphValue.documents[0].document.parameters[IndexValue].value.value
        assert isinstance(Edited, float)
        Written = PrepNestedAsm(DocumentValue, Locator, 1794011937)[0][1].BytesValue
        assert Written != Baseline
        Reopened = OpenDocument(BytesIO(Written), source_format=KPartFormatId)
        ParameterId = Reopened.sketches[0].parameter_ids[IndexValue]
        assert (
            Reopened.parameter(ParameterId).attributes["native_value"] == Edited * 0.001
        )
