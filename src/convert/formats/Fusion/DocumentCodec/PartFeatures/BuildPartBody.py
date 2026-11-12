from time import time_ns as ReadTimeNano

from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Model.AuthorPolicy import AuthorPolicy
from convert.formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.EmitPartHist import (
    EmitPartHist,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.BuildShape import (
    BuildShape,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.SolvePart import SolvePart


def BuildPartBody(
    SpecValue: DocumentSpec, Design: DesignResult
) -> tuple[ContainerPart, ...]:
    if Design.BrepPart is None:
        raise ValueError("Fusion part authoring requires a BRep part identity")
    Policy = AuthorPolicy()
    if Policy.BodyKey != 0:
        raise ValueError("Fusion part journals claim body tag zero first")
    BaseValue, Stages = SolvePart(SpecValue)
    Solids = (BaseValue, *(Stage.After for Stage in Stages))
    StateIds = (Policy.HistoryCurrentId, *(Stage.StateId for Stage in Stages))
    Payload = EmitPartHist(
        tuple((BuildShape(Solid),) for Solid in Solids),
        StateIds,
        Policy.HistoryInitialId,
        float(ReadTimeNano() // 1000),
    )
    return (ContainerPart("Breps.BlobParts/" + Design.BrepPart, Payload),)
