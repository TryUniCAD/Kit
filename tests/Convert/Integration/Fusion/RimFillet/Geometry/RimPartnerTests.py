from pytest import raises as RaisesError

from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from tests.Convert.Integration.Fusion.RimFillet.Geometry.ChangeRimModel import (
    ChangeRimModel,
)
from tests.Convert.Integration.Fusion.RimFillet.Policy.ReadPolicyCases import (
    ReadPolicyCases,
)


# invalid partner incidence must fail at the existing complete archive encoder boundary
def CheckPartnerBad() -> None:
    Sample = next(
        Value for Value in ReadPolicyCases() if Value.CaseName == "source-discovery-01"
    )
    Encoded = Sample.Source.read_bytes()
    Model = ReadDocument(Encoded)
    Changed = ChangeRimModel(Model, "coedge_partner")
    with RaisesError(ValueError, match="partners"):
        _ = EmitParsed(Changed)
    assert Sample.Source.read_bytes() == Encoded
