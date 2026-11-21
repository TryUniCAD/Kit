from __future__ import annotations

from typing import cast as CastValue

from convert.adapters.solidworks.Container.Container import SldprtArchive
from tests.Convert.Solidworks.Research.Composition.NodeFields import ReadFields
from tests.Convert.Solidworks.Research.Composition.ProfileRoots import ReadProfiles


# serialized canonical views need distinct objects with active rotation payloads after decoding
def HasViewTargets(ArchiveFile: SldprtArchive, CodecReg: object) -> bool:
    ModelRoot, _ = ReadProfiles(ArchiveFile, CodecReg)
    Entries = CastValue(list[dict[str, object]], ReadFields(ModelRoot)["f9f8"])
    Nodes = [Entry["o"] for Entry in Entries]
    if len(Nodes) != 10 or len({id(ViewNode) for ViewNode in Nodes}) != 10:
        return False
    if any(getattr(ViewNode, "cls", None) != "moView_c" for ViewNode in Nodes):
        return False
    if [ReadFields(ViewNode)["f360"] for ViewNode in Nodes] != list(range(10)):
        return False
    Transforms = [
        CastValue(dict[str, object], ReadFields(ViewNode)["f368"]) for ViewNode in Nodes
    ]
    return [Transform["has_matrix"] for Transform in Transforms] == [0, 0] + [1] * 8
