from pathlib import Path as FilePath

from convert import open_document as OpenDoc
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KResolvedFeaturesStream
from interchange.Features.FeatureAngleRev import AngularRevolve
from tests.Convert.Solidworks.Research.AdapterBridge.PrepareProbe import PrepareProbe
from tests.Convert.Solidworks.Research.AdapterBridge.Revolve.CheckRevDrivers import (
    CheckRevDrivers,
)
from tests.Convert.Solidworks.Research.AdapterBridge.Revolve.MakeRevCase import (
    MakeRevCase,
)


# deterministic revolve routes must retain separate angular drivers and vary the actual resolved stream length
def TestRevRegistry(TmpPath: FilePath) -> None:
    Sizes: list[int] = []
    for TwoSides, Label in ((False, "Single"), (True, "Double")):
        ModeValue = "two_sided" if TwoSides else "one_sided"
        Request = MakeRevCase(Label, ModeValue)
        Target = TmpPath / (Label + ".SLDPRT")
        RawValue = PrepareProbe(Request, Target, 1795000061)
        for SourceValue in (Target, RawValue):
            Parsed = OpenDoc(
                SourceValue, source_format="solidworks.sldprt", strict=True
            )
            assert len(Parsed.bodies) == 1 and len(Parsed.sketches[0].constraints) == 4
            CheckRevDrivers(Parsed, ModeValue, TwoSides)
        Archive = SldprtArchive.from_bytes(RawValue)
        Sizes.append(len(Archive.require(KResolvedFeaturesStream)))
    assert Sizes[1] > Sizes[0]


# the authored square must retain the equal relation and its single total mid plane driver
def TestSqRegistry(TmpPath: FilePath) -> None:
    Request = MakeRevCase("Square", "symmetric_full", IsSquare=True)
    Target = TmpPath / "Square.SLDPRT"
    _ = PrepareProbe(Request, Target, 1795000061)
    Parsed = OpenDoc(Target, strict=True)
    (Sketch,) = Parsed.sketches
    (Feature,) = Parsed.feature_timeline
    Definition = Feature.definition
    assert isinstance(Definition, AngularRevolve)
    assert (
        Definition.SideMode == "symmetric_full"
        and Definition.AgainstParameterId is None
    )
    assert len(Sketch.constraints) == 5
    (EqualRule,) = (
        Relation for Relation in Sketch.constraints if Relation.kind == "equal"
    )
    assert tuple(Reference.entity_id for Reference in EqualRule.references) == (
        Sketch.entities[3].id,
        Sketch.entities[0].id,
    )
    (Driver,) = (
        Param for Param in Parsed.parameters if Param.id == Definition.AlongParameterId
    )
    assert Driver.name == "D1" and Driver.value.value == 1.25
    assert Driver.owner_id == Feature.id and len(Parsed.bodies) == 1
