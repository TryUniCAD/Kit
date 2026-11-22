from dataclasses import replace as ReplaceValue

from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismIds import PrismIds
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


# reconstructed geometry must retain the entity identities assigned by the source application
def ApplyPrismIds(
    Records: tuple[GeometryRecord, ...], Tracking: PrismIds
) -> tuple[GeometryRecord, ...]:
    Identifiers = dict(Tracking.Entries)
    return tuple(
        (
            ReplaceValue(
                Record,
                Fields=(Record.Fields[0], Identifiers[Index], *Record.Fields[2:]),
            )
            if Index in Identifiers
            else Record
        )
        for Index, Record in enumerate(Records)
    )
