from dataclasses import replace as ReplaceValue
from math import inf as PositiveInfinity, isclose as IsClose, nextafter as NextFloat

from interchange.document.Models.DocumentModel import CadDocument


# an adjacent representable edit must change the emitted unit while remaining inside the former tolerance
def CheckDriverEdit(Document: CadDocument, IndexValue: int) -> CadDocument:
    GraphValue = Document.assembly
    assert GraphValue is not None
    (Member,) = GraphValue.documents
    PartValue = Member.document
    Drivers = list(PartValue.parameters)
    Driver = Drivers[IndexValue]
    LengthValue = Driver.value.value
    assert type(LengthValue) is float
    NewLength = NextFloat(LengthValue, PositiveInfinity)
    MetresValue, NewMetres = LengthValue * 0.001, NewLength * 0.001
    assert NewMetres != MetresValue
    assert IsClose(NewMetres, MetresValue, rel_tol=1e-12, abs_tol=1e-14)
    Drivers[IndexValue] = ReplaceValue(
        Driver, value=ReplaceValue(Driver.value, value=NewLength)
    )
    Modified = ReplaceValue(PartValue, parameters=tuple(Drivers))
    return ReplaceValue(
        Document,
        assembly=ReplaceValue(
            GraphValue, documents=(ReplaceValue(Member, document=Modified),)
        ),
    )
