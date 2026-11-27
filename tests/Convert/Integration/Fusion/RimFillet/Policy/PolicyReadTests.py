from hashlib import sha256 as HashData

from pytest import mark as TestMark

from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimPolicy import (
    CheckRimPolicy,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.ReadRimContext import (
    ReadRimContext,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.ReadRimParams import (
    ReadRimParams,
)
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Integration.Fusion.RimFillet.Policy.ReadPolicyCases import (
    ReadPolicyCases,
)
from tests.Convert.Integration.Fusion.RimFillet.Policy.RimPolicyCase import (
    RimPolicyCase,
)


# complete native archives must preserve every actual parameter rather than only the final radius
@TestMark.parametrize("Sample", ReadPolicyCases())
def CheckPolicyRead(Sample: RimPolicyCase) -> None:
    Encoded = Sample.Source.read_bytes()
    assert HashData(Encoded).hexdigest() == Sample.Digest
    Model = ReadDocument(Encoded)
    Graph = BuildGraph(Model)
    Context = ReadRimContext(Graph)
    CheckRimPolicy(Model, Graph, Context)
    Projected = ReadRimParams(Graph, Context)
    Values = {Value.name: Value for Value in Projected}
    assert len(Projected) == len(Sample.Parameters)
    assert len({Value.id for Value in Projected}) == len(Projected)
    for ParamName, Amount, UnitName, Expression in Sample.Parameters:
        Value = Values[ParamName]
        assert isinstance(Value.value.value, (int, float))
        assert abs(Value.value.value - Amount * (10 if UnitName == "mm" else 1)) < 1e-9
        assert Value.expression is not None and Value.expression.source == Expression
    assert (
        next(
            Value for Value in Projected if Value.id == Context.RadiusParam.Identity
        ).owner_id
        == Context.Feature.Identity
    )
    assert (
        next(
            Value for Value in Projected if Value.id == Context.WeightParam.Identity
        ).owner_id
        == Context.Feature.Identity
    )
    assert Model == ReadDocument(Encoded)
