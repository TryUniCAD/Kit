from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath

from pytest import raises as RaisesError

from convert import open_document as OpenDocument
from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import (
    ReadRigidXform,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireRecord
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.PrepareNestedAssembly import (
    PrepNestedAsm,
)
from interchange.document.Models.DocumentModel import CadDocument
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


# the fixture changes only one explicit portable translation
def WithTestOffset(LengthValue: float) -> CadDocument:
    DocumentValue = MakeNestDoc()
    GraphValue = DocumentValue.assembly
    assert GraphValue is not None
    FirstValue, *Remaining = GraphValue.instances
    MatrixValue = list(FirstValue.transform.values)
    MatrixValue[3] = LengthValue
    Changed = ReplaceValue(
        FirstValue,
        transform=ReplaceValue(FirstValue.transform, values=tuple(MatrixValue)),
    )
    return ReplaceValue(
        DocumentValue,
        assembly=ReplaceValue(GraphValue, instances=(Changed, *Remaining)),
    )


# a nearby native word can represent precisely nine millimetres
def TestNineOffset(TmpPath: FilePath) -> None:
    Candidates = PrepNestedAsm(
        WithTestOffset(9.0), r"C:\KitNestedQueue\QueueFrame.SLDASM", 1794011937
    )
    Translations = {
        Lengths[0]
        for _, Candidate in Candidates
        for Reference in Candidate.ReferenceValues
        for _, Lengths in (
            ReadRigidXform(RequireRecord(Reference.FieldsValue["f360"])),
        )
    }
    assert 0.009 in Translations
    assert (9.0 * 0.001) not in Translations
    for Locator, Candidate in Candidates:
        _ = (TmpPath / Locator.name).write_bytes(Candidate.BytesValue)
    Reopened = OpenDocument(TmpPath / Candidates[-1][0].name, strict=True)
    assert Reopened.assembly is not None
    (PlateValue,) = tuple(
        Value for Value in Reopened.assembly.instances if Value.name == "QueuePlate-1"
    )
    assert PlateValue.transform.values[3] == 9.0


# a physical placement word must invert to the actual authored translation
def TestExactOffset() -> None:
    with RaisesError(ValueError, match="cannot preserve the authored translation"):
        _ = PrepNestedAsm(
            WithTestOffset(7.9338167953905945),
            r"C:\KitNestedQueue\QueueFrame.SLDASM",
            1794011937,
        )
