from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismIds import PrismIds
from convert.Formats.Fusion.BrepCodec.Prism.PrismLayout import KFirstAttribute
from convert.Formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmInt
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


# current topology identities are source data rather than empty defaults after native edits
def ReadPrismIds(Table: AsmTable, Mapping: dict[int, int]) -> PrismIds:
    return PrismIds(
        tuple(
            (Index, Value)
            for Index in range(KFirstAttribute)
            if Index != 1
            and (Value := ReadAsmInt(Table.Records[Mapping[Index]], 1)) != -1
        )
    )
