from pathlib import Path as FilePath

from convert.adapters.Fusion.Native.Circular.RimPolicy.ReadRimContext import (
    ReadRimContext,
)
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField
from tests.Convert.Integration.Fusion.DualSide.ChangeDualMass import ChangeDualMass
from tests.Convert.Integration.Fusion.RimFillet.Geometry.ChangeRimModel import (
    ChangeRimModel,
)
from tests.Convert.Integration.Fusion.RimFillet.Policy.ReadPolicyCases import (
    ReadPolicyCases,
)


# public refusal probes must contain actual serialized native corruptions rather than mocked checker failures
def MakePublicBad(Family: str, CaseName: str) -> bytes:
    if Family == "policy":
        return (
            FilePath(__file__).resolve().parents[6]
            / "re/Fusion/DecodedPromotion20261127/RimFilletPolicy/Counterexamples"
            / (CaseName + ".f3d")
        ).read_bytes()
    Sample = next(
        Value for Value in ReadPolicyCases() if Value.CaseName == "source-discovery-01"
    )
    Model = ReadDocument(Sample.Source.read_bytes())
    if Family == "geometry":
        return EmitParsed(ChangeRimModel(Model, CaseName))
    Context = ReadRimContext(BuildGraph(Model))
    Cache = Context.Extrusion.BodyNode.Fields["cache"]
    assert isinstance(Cache, ValueObject)
    FieldName, _, AxisName = CaseName.partition(":")
    return EmitParsed(
        ChangeField(
            Model,
            Context.Extrusion.BodyNode.ObjectId,
            "cache",
            ChangeDualMass(Cache, FieldName, AxisName),
        )
    )
