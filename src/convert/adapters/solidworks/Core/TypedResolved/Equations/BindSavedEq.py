from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.Partition.PartTopology import (
    ActivePartMass,
    PartTopology,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BindBodyName import (
    BindBodyName,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadNamedBody import (
    ReadNamedBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Equations.CheckEqShape import (
    CheckEqShape,
)
from convert.adapters.solidworks.Core.TypedResolved.Equations.WidthDepthLink import (
    WidthDepthLink,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# the equation and the single active named body must use the same physical feature and configuration
def BindSavedEq(
    Document: CadDocument, Model: NativeModel, Relation: WidthDepthLink
) -> CadDocument:
    Graph = ReadNamedBody(
        Document,
        Relation.SourceValue,
        Model.active_configuration_id,
        LinkedValue=Relation.LinkValue,
    )
    if Graph.FeatureId != Relation.DepthFeature:
        raise ValueError("saved width-depth equation targets a different body creator")
    Bound = BindBodyName(Document, Graph)
    Actual = Bound.brep
    if Actual is None:
        raise ValueError("saved width-depth body lacks its complete physical boundary")
    (BodyValue,) = Bound.bodies
    AreaValue = CheckEqShape(Actual, Model)
    Topology, MassValue = ActivePartMass(
        Actual, PartTopology(Actual, BodyValue.id, BodyValue.topology), BodyValue.id
    )
    if MassValue is None:
        raise ValueError("saved width-depth body lacks closed solid measures")
    NamedBody = ReplaceValue(
        BodyValue,
        topology=ReplaceValue(Topology, surface_area=AreaValue, valid=True),
        attributes=FreezeMapping(
            {
                **BodyValue.attributes,
                "native_object_id": Graph.FeatureId,
                "solidworks.body_centroid_mm": MassValue.Centroid,
            }
        ),
    )
    return ReplaceValue(Bound, bodies=(NamedBody,))
