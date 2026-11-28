from convert.Formats.Fusion.BrepCodec.Journal.Attributes.MaterialAttrib import (
    KMaterialFamily,
)
from convert.Formats.Fusion.BrepCodec.Journal.Validation.ReadLiveRef import ReadLiveRef
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


# face appearance must follow a reciprocal attribute chain in each live revision
def CheckFaceMat(
    Records: tuple[AsmRecord, ...],
    Versions: dict[int, int],
    Aliases: tuple[int, ...],
) -> None:
    for SlotId, Revision in Versions.items():
        Record = Records[Revision]
        if Record.Name != "ATTRIB_CUSTOM-attrib" or Record.Tokens[5] != (
            7,
            KMaterialFamily,
        ):
            continue
        OwnerId = ReadLiveRef(Record, 4, Aliases)
        if OwnerId == -1 or Records[Versions[OwnerId]].Name != "face":
            raise ValueError("Fusion journal face material requires a face owner")
        Owner = Records[Versions[OwnerId]]
        Current = SlotId
        Visited: set[int] = set()
        while Current != -1:
            Linked = Records[Versions[Current]]
            Prior = ReadLiveRef(Linked, 3, Aliases)
            if (
                Current in Visited
                or ReadLiveRef(Linked, 4, Aliases) != OwnerId
                or (
                    Prior != -1
                    and ReadLiveRef(Records[Versions[Prior]], 2, Aliases) != Current
                )
            ):
                raise ValueError("Fusion journal face material chain is not reciprocal")
            Visited.add(Current)
            if Prior == -1 and ReadLiveRef(Owner, 0, Aliases) != Current:
                raise ValueError("Fusion journal face material chain is not reciprocal")
            Current = Prior
        NextId = ReadLiveRef(Record, 2, Aliases)
        if NextId != -1:
            Linked = Records[Versions[NextId]]
            if (
                ReadLiveRef(Linked, 3, Aliases) != SlotId
                or ReadLiveRef(Linked, 4, Aliases) != OwnerId
            ):
                raise ValueError("Fusion journal face material chain is not reciprocal")
