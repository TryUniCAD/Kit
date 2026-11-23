from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.MakeLocalCyl import (
    MakeLocalCyl,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeLocalPocket import (
    MakeLocalPocket,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeLocalPrism import (
    MakeLocalPrism,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.BindLocalAttrs import (
    BindLocalAttrs,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.EncodeLocalBody import (
    EncodeLocalBody,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.LocalBodyOwner import (
    LocalBodyOwner,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface
from interchange.brep.Topology.BrepModel import BrepModel


# actual feature atom and log owners must precede attributed body serialization
def EncodeImpBody(
    ModelValue: BrepModel,
    KeyValue: str,
    FeatureValue: ArchiveNode,
    AtomId: int,
    BodyStamp: int,
    OwnedBody: bool,
) -> bytes:
    if type(OwnedBody) is not bool:
        raise TypeError("local import attributes require an explicit boolean")
    IsPeriodic = any(
        isinstance(Surface, CylinderSurface) for Surface in ModelValue.surfaces
    )
    IsPocket = not IsPeriodic and any(
        not LoopValue.outer for LoopValue in ModelValue.loops
    )
    if IsPeriodic and OwnedBody:
        raise ValueError("local import attributes require a planar body")
    if IsPeriodic:
        NodesValue = MakeLocalCyl(ModelValue)
    elif IsPocket:
        if OwnedBody:
            raise ValueError("local pocket does not admit attributed body owners")
        NodesValue = MakeLocalPocket(ModelValue)
    else:
        NodesValue = MakeLocalPrism(ModelValue)
    if OwnedBody:
        NameValue = ReadNodeName(FeatureValue)
        if NameValue != KeyValue:
            raise ValueError(
                "local body attributes require the actual feature storage key"
            )
        OwnerValue = LocalBodyOwner(
            NameValue, FieldInt(FeatureValue.FieldsValue, "f08"), AtomId, BodyStamp
        )
        NodesValue = BindLocalAttrs(NodesValue, OwnerValue)
    return EncodeLocalBody(KeyValue, NodesValue, AllowPocket=IsPocket)
