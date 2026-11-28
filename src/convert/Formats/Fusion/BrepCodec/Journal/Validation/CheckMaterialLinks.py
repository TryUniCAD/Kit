from convert.Formats.Fusion.BrepCodec.Journal.Attributes.MaterialAttrib import (
    KMaterialFamily,
)
from convert.Formats.Fusion.BrepCodec.Journal.Validation.ReadLiveRef import ReadLiveRef
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


# face appearance must follow a reciprocal attribute chain in each live revision
def CheckMaterialLinks(
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
        Seen: set[int] = set()
        while Current != -1:
            Link = Records[Versions[Current]]
            Prior = ReadLiveRef(Link, 3, Aliases)
            if (
                Current in Seen
                or ReadLiveRef(Link, 4, Aliases) != OwnerId
                or (
                    Prior != -1
                    and ReadLiveRef(Records[Versions[Prior]], 2, Aliases) != Current
                )
            ):
                raise ValueError("Fusion journal face material chain is not reciprocal")
            Seen.add(Current)
            if Prior == -1 and ReadLiveRef(Owner, 0, Aliases) != Current:
                raise ValueError("Fusion journal face material chain is not reciprocal")
            Current = Prior
        Next = ReadLiveRef(Record, 2, Aliases)
        if Next != -1:
            Link = Records[Versions[Next]]
            if (
                ReadLiveRef(Link, 3, Aliases) != SlotId
                or ReadLiveRef(Link, 4, Aliases) != OwnerId
            ):
                raise ValueError("Fusion journal face material chain is not reciprocal")
