from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarChild
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


# child datum owners must come from the same immutable bytes as the already loaded public document
def ReadMateChild(SourcePath: FilePath, SourceHash: str) -> PlanarChild:
    BufferValue = SourcePath.read_bytes()
    if HashBytes(BufferValue).hexdigest() != SourceHash:
        raise ValueError("typed mate child changed after component document loading")
    Archive = SldprtArchive.from_bytes(BufferValue)
    LinkValue = ReadNativeLink(Archive, 0)
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
