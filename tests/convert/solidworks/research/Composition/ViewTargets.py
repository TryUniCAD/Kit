from __future__ import annotations

from typing import cast as CastValue

from convert.adapters.solidworks.container.Container import SldprtArchive
from tests.convert.solidworks.research.Composition.NodeFields import ReadFields
from tests.convert.solidworks.research.Composition.ProfileRoots import ReadProfiles


# serialized canonical views need distinct objects with active rotation payloads after decoding
def HasViewTargets(ArchiveFile: SldprtArchive, CodecReg: object) -> bool:
    ModelRoot, _ = ReadProfiles(ArchiveFile, CodecReg)
    Entries = CastValue(list[dict[str, object]], ReadFields(ModelRoot)["f9f8"])
    Nodes = [Entry["o"] for Entry in Entries]
    if len(Nodes) != 10 or len({id(Node) for Node in Nodes}) != 10:
        return False
    if any(getattr(Node, "cls", None) != "moView_c" for Node in Nodes):
        return False
    if [ReadFields(Node)["f360"] for Node in Nodes] != list(range(10)):
        return False
    Transforms = [
        CastValue(dict[str, object], ReadFields(Node)["f368"]) for Node in Nodes
    ]
    return [Transform["has_matrix"] for Transform in Transforms] == [0, 0] + [1] * 8
