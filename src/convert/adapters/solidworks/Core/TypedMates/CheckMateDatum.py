from convert.adapters.solidworks.Assembly.PlanarMates.PlanarEndpoint import (
    PlanarEndpoint,
)
from convert.adapters.solidworks.Core.TypedMates.PublicMateEnv import PublicMateEnv


# neutral entity references must resolve to the actual plane in the linked public component document
def CheckMateDatum(Endpoint: PlanarEndpoint, EnvValue: PublicMateEnv) -> None:
    Document = EnvValue.DocumentsValue[Endpoint.ChildDefinitionId]
    PlaneId = f"sldprt:plane:{Endpoint.DatumFeatureId}"
    Matches = tuple(
        Value
        for Value in Document.support_planes
        if Value.id == PlaneId and Value.name == Endpoint.DatumName
    )
    if len(Matches) != 1:
        raise ValueError(
            "typed mate datum is absent or ambiguous in the linked public child"
        )
