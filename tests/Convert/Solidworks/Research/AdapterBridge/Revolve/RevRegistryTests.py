from io import BytesIO
from pathlib import Path as FilePath
from unittest.mock import patch as Patch

from convert import open_document as OpenDoc
from convert import write_document as WriteDoc
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KResolvedFeaturesStream
from interchange.Features.FeatureAngleRev import AngularRevolve
from tests.Convert.Solidworks.Research.AdapterBridge.Revolve.CheckRevDrivers import (
    CheckRevDrivers,
)
from tests.Convert.Solidworks.Research.AdapterBridge.Revolve.MakeRevCase import (
    MakeRevCase,
)


# public path and stream publication must retain separate angular drivers and vary the actual resolved stream length
def TestRevRegistry(TmpPath: FilePath) -> None:
    Sizes: list[int] = []
    for TwoSides, Label in ((False, "Single"), (True, "Double")):
        ModeValue = "two_sided" if TwoSides else "one_sided"
        Request = MakeRevCase(Label, ModeValue)
        Target = TmpPath / (Label + ".SLDPRT")
        Policy = {"require_native_transfers": True}
        Stream = BytesIO()
        with Patch(
            "convert.adapters.solidworks.Core.Writing.EmitNativeMut.ReadTime",
            return_value=1795000061,
        ):
            Written = WriteDoc(Request, Target, allow_carrier=False, values=Policy)
            Named = WriteDoc(
                Request,
                Stream,
                destination_format="solidworks.sldprt",
                allow_carrier=False,
                values={**Policy, "final_destination": str(Target)},
            )
        Bytes = Stream.getvalue()
        assert Target.read_bytes() == Bytes
        assert Written.bytes_written == Named.bytes_written == len(Bytes)
        assert Request.capabilities <= Written.native_capabilities
        assert Request.capabilities <= Named.native_capabilities
        assert not Written.dropped and not Named.dropped
        Parsed = OpenDoc(Target, strict=True)
        assert len(Parsed.bodies) == 1 and len(Parsed.sketches[0].constraints) == 4
        CheckRevDrivers(Parsed, ModeValue, TwoSides)
        Archive = SldprtArchive.from_bytes(Bytes)
        Sizes.append(len(Archive.require(KResolvedFeaturesStream)))
    assert Sizes[1] > Sizes[0]


# the public square profile must retain the authored equal pair and one total mid plane driver
def TestSqRegistry(TmpPath: FilePath) -> None:
    Request = MakeRevCase("Square", "symmetric_full", IsSquare=True)
    Target = TmpPath / "Square.SLDPRT"
    Written = WriteDoc(
        Request, Target, allow_carrier=False, values={"require_native_transfers": True}
    )
    assert Request.capabilities <= Written.native_capabilities and not Written.dropped
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
