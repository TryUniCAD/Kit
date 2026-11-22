from math import fsum as SumValues, isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylMateIn import (
    CylMateIn,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.BindConcSide import (
    BindConcSide,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.CylMateEnd import (
    CylMateEnd,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.CylMatePlan import (
    CylMatePlan,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.ReadConcEnd import (
    ReadConcEnd,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.ReadConcMate import (
    ReadConcMate,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import (
    ReadAsmModel,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Placements.ReadAsmPlace import (
    ReadAsmPlace,
)
from interchange.document.Models.DocumentModel import CadDocument


# the ordinary writer requires the existing authored positions to satisfy the signed coaxial relation
def CheckConcPose(First: CylMateEnd, Second: CylMateEnd, Alignment: int) -> None:
    Product = SumValues(
        FirstValue * SecondValue
        for FirstValue, SecondValue in zip(
            First.AxisValue, Second.AxisValue, strict=True
        )
    )
    Offset = tuple(
        SecondValue - FirstValue
        for FirstValue, SecondValue in zip(
            First.OriginValue, Second.OriginValue, strict=True
        )
    )
    Slide = SumValues(
        Value * AxisItem
        for Value, AxisItem in zip(Offset, First.AxisValue, strict=True)
    )
    if not IsClose(
        Product, 1.0 if Alignment == 1 else -1.0, rel_tol=1e-10, abs_tol=1e-12
    ) or any(
        not IsClose(Value - Slide * AxisItem, 0.0, abs_tol=1e-12)
        for Value, AxisItem in zip(Offset, First.AxisValue, strict=True)
    ):
        raise ValueError(
            "concentric placements must satisfy explicit coaxial alignment"
        )


# assembly planning binds only the actual repeated child and translates the fixed slot into endpoint order
def PlanCylMate(
    Document: CadDocument,
    ChildDocument: CadDocument,
    Candidate: PartCandidate,
    FaceTag: int,
) -> CylMatePlan:
    Model = ReadAsmModel(Document)
    if len(Model.Occurrences) != 2 or Document.parameters:
        raise ValueError(
            "concentric preparation requires two direct occurrences and no mate dimensions"
        )
    if ChildDocument is not Model.ChildDocument:
        raise ValueError(
            "concentric candidate requires the actual embedded child document"
        )
    MateValue, FirstEntity, SecondEntity, Alignment, Locked = ReadConcMate(Model)
    SideValue, Surface, FaceValue = BindConcSide(ChildDocument, Candidate, FaceTag)
    FirstOccurrence, SecondOccurrence = Model.Occurrences
    Placements = (ReadAsmPlace(FirstOccurrence), ReadAsmPlace(SecondOccurrence))
    First, Second = (
        ReadConcEnd(Entity, Model, Placements, FaceValue, SideValue.id, Surface.radius)
        for Entity in (FirstEntity, SecondEntity)
    )
    if First.OccurrenceValue is Second.OccurrenceValue:
        raise ValueError("concentric endpoints must select two distinct occurrences")
    CheckConcPose(First, Second, Alignment)
    Indexes = (First.IndexValue, Second.IndexValue)
    return CylMatePlan(
        Model,
        MateValue,
        Candidate,
        SideValue,
        FaceValue,
        Placements,
        (First, Second),
        Indexes,
        CylMateIn(MateValue.name, Alignment, Locked, Indexes.index(Model.FixedIndex)),
    )
