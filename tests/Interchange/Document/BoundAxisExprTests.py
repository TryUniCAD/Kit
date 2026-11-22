from dataclasses import replace as ReplaceValue

from pytest import raises as Raises

from interchange import CadDocument
from interchange.document.Models.DocumentError import DocumentError
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordParameter import Expression
from tests.Interchange.Document.BoundPlaneAxisTests import BuildBoundAxis, ReadAxisDoc


# the evaluated station drives geometry while the original typed expression remains editable
def CheckAxisExpr() -> None:
    Document = BuildBoundAxis()
    StartValue, EndValue = Document.parameters
    Formula = Expression("start - 12 mm", (StartValue.id,), "source")
    Expressed = ReplaceValue(EndValue, expression=Formula)
    Stored = ReplaceValue(Document, parameters=(StartValue, Expressed))
    Loaded = CadDocument.from_json(Stored.to_json())
    assert Loaded.parameters[1].expression == Formula
    assert ReadAxisDoc(Loaded) == (
        SpaceVector(8.0, 18.0, 22.0),
        SpaceVector(8.0, 6.0, 22.0),
    )
    NewStart = ReplaceValue(StartValue, value=ReplaceValue(StartValue.value, value=5.0))
    NewEnd = ReplaceValue(Expressed, value=ReplaceValue(Expressed.value, value=-0.7))
    Updated = CadDocument.from_json(
        ReplaceValue(Stored, parameters=(NewStart, NewEnd)).to_json()
    )
    assert Updated.parameters[1].expression == Formula
    assert ReadAxisDoc(Updated) == (
        SpaceVector(8.0, 19.0, 22.0),
        SpaceVector(8.0, 7.0, 22.0),
    )
    Dangling = ReplaceValue(
        Expressed, expression=ReplaceValue(Formula, parameter_ids=("missing",))
    )
    Broken = ReplaceValue(Stored, parameters=(StartValue, Dangling))
    with Raises(DocumentError, match="references missing parameter missing"):
        _ = CadDocument.from_json(Broken.to_json())
