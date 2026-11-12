from convert.formats.Fusion.BrepCodec.Journal.Validation.EntityRefRules import (
    KEntityRefRules,
)
from convert.formats.Fusion.BrepCodec.Journal.Validation.RequiredRefs import (
    KRequiredRefs,
)
from convert.formats.Fusion.BrepCodec.Journal.Validation.ResolveSlot import ResolveSlot
from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckLiveUses import (
    CheckLiveUses,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.formats.Fusion.BrepCodec.Journal.Round.CheckLiveFaces import CheckLiveFaces


def CheckLiveRefs(
    Records: tuple[AsmRecord, ...], Versions: dict[int, int], Aliases: tuple[int, ...]
) -> None:
    for Revision in Versions.values():
        Record = Records[Revision]
        Rules = KEntityRefRules[Record.Name]
        for Index, (TagValue, Value) in enumerate(Record.Tokens):
            if TagValue != 12:
                continue
            if (
                type(Value) is not int
                or Value < -1
                or Value >= len(Records)
                or Index not in Rules
            ):
                raise ValueError("Invalid Fusion journal entity reference")
            if Value == -1:
                if Index in KRequiredRefs.get(Record.Name, ()):
                    raise ValueError("Missing required Fusion topology reference")
                continue
            Target = ResolveSlot(Aliases, Value)
            Allowed = Rules[Index]
            if (
                Record.Name == "ATTRIB_CUSTOM-attrib"
                and Index == 4
                and Record.Tokens[5]
                in ((7, "generic_tag_attrib_def"), (7, "sketch_attrib_def"))
            ):
                Allowed = (*Allowed, "vertex")
            if Target not in Versions or Records[Versions[Target]].Name not in Allowed:
                raise ValueError(
                    "Fusion historical entity reference is absent or class-incompatible"
                )
    CheckLiveUses(Records, Versions, Aliases)
    CheckLiveFaces(Records, Versions, Aliases)
