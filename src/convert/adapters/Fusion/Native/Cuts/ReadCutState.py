from convert.Formats.Fusion.BrepCodec.Journal.Planar.MakeLiveTable import MakeLiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode


# each requested extrusion boundary must resolve to one untransformed live body
def ReadCutState(History: JournalModel, StateId: int) -> tuple[LiveTable, int]:
    Table = MakeLiveTable(History, StateId)
    Bodies = tuple(
        Reference
        for Reference in Table.LiveSlots
        if isinstance(Table.Entities[Reference], BodyNode)
    )
    if len(Bodies) != 1:
        raise ValueError("Native cut state has no unique body")
    BodyValue = Table.Entities[Bodies[0]]
    if not isinstance(BodyValue, BodyNode) or BodyValue.TransformRef != -1:
        raise ValueError("Native cut state has unsupported body placement")
    return Table, Bodies[0]
