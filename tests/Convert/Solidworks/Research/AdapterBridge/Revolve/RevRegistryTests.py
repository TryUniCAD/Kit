from io import BytesIO
from pathlib import Path as FilePath
from unittest.mock import patch as Patch

from convert import open_document as OpenDoc
from convert import write_document as WriteDoc
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KResolvedFeaturesStream
from interchange.Features.FeatureAngleRev import AngularRevolve
from tests.Convert.Solidworks.Research.AdapterBridge.Revolve.MakeRevCase import (
    MakeRevCase,
)


# public path and stream publication must retain separate angular drivers and vary the actual resolved stream length
def TestRevRegistry(TmpPath: FilePath) -> None:
    Sizes: list[int] = []
    for TwoSides, Label in ((False, "Single"), (True, "Double")):
        Request = MakeRevCase(Label, TwoSides)
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
        (Feature,) = Parsed.feature_timeline
        Definition = Feature.definition
        assert isinstance(Definition, AngularRevolve)
        assert Definition.SideMode == ("two_sided" if TwoSides else "one_sided")
        Drivers = {Driver.id: Driver for Driver in Parsed.parameters}
        Along = Drivers[Definition.AlongParameterId]
        assert Along.name == "D1" and Along.value.value == 1.25
        assert Along.owner_id == Feature.id
        Against = Definition.AgainstParameterId
        if TwoSides:
            assert Against is not None and Against != Along.id
            assert (
                Drivers[Against].name == "D2" and Drivers[Against].value.value == 0.875
            )
            assert Drivers[Against].owner_id == Feature.id
        else:
            assert Against is None
        Archive = SldprtArchive.from_bytes(Bytes)
        Sizes.append(len(Archive.require(KResolvedFeaturesStream)))
    assert Sizes[1] > Sizes[0]
