from hashlib import sha256 as HashBytes

from pytest import mark as MarkTests

from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimLive import CheckRimLive
from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimSnaps import (
    CheckRimSnaps,
)
from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimMass import CheckRimMass
from convert.adapters.Fusion.Native.Circular.RimPolicy.ReadRimContext import (
    ReadRimContext,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimPolicy import (
    CheckRimPolicy,
)
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Integration.Fusion.RimFillet.Policy.ReadPolicyCases import (
    ReadPolicyCases,
)
from tests.Convert.Integration.Fusion.RimFillet.Policy.RimPolicyCase import (
    RimPolicyCase,
)


# all original reserved depth edited and later native sources must pass complete composed read only qualification
@MarkTests.parametrize("Sample", ReadPolicyCases())
def CheckRimArchive(Sample: RimPolicyCase) -> None:
    Encoded = Sample.Source.read_bytes()
    assert HashBytes(Encoded).hexdigest() == Sample.Digest
    Model = ReadDocument(Encoded)
    Graph = BuildGraph(Model)
    Context = ReadRimContext(Graph)
    CheckRimPolicy(Model, Graph, Context)
    Shape = ReadCircle(Graph, Context.Extrusion)
    Prior, Current = CheckRimLive(Model, Graph, Context, Shape)
    CheckRimSnaps(Model, Graph, Context, Shape, Prior)
    CheckRimMass(
        Context,
        Shape.Geometry.radius,
        NumberValue(Context.Extrusion.Along.Fields["value"]) * 10,
        NumberValue(Context.Radius.Fields["value"]) * 10,
    )
    assert len(Prior.Entities) == 36 and len(Current.Entities) == 45
    assert Model == ReadDocument(Encoded)
