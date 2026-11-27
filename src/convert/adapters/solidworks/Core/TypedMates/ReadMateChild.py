from hashlib import sha256 as HashBytes

from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarChild
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedMates.ColdMateLayout import (
    HasColdStreams,
    KColdChildStreams,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


# child datum owners must come from the same immutable bytes as the already loaded public document
def ReadMateChild(
    BufferValue: bytes, SourceHash: str, *, ColdRequired: bool = False
) -> PlanarChild:
    if HashBytes(BufferValue).hexdigest() != SourceHash:
        raise ValueError("typed mate child changed after component document loading")
    Archive = SldprtArchive.from_bytes(BufferValue)
    if ColdRequired and not HasColdStreams(Archive, KColdChildStreams):
        raise ValueError("cold planar group requires an ordinary cold child archive")
    LinkValue = ReadNativeLink(Archive, 0, RectangleDims=True)
    if LinkValue.ConfigValue.RootValue.ClassValue != RuntimeClass("moPart_c", 1):
        raise ValueError("typed mate child is not an ordinary part")
    NodesValue = tuple(
        Value
        for Value in LinkValue.ResolvedValue.RootsValue
        if Value is not None and Value.ClassValue == RuntimeClass("moRefPlane_c", 1)
    )
    DatumNodes = {FieldInt(Value.FieldsValue, "f08"): Value for Value in NodesValue}
    if len(DatumNodes) != len(NodesValue):
        raise ValueError("typed mate child datum identifiers are ambiguous")
    return PlanarChild(LinkValue.ConfigValue.HeaderValue, DatumNodes)
