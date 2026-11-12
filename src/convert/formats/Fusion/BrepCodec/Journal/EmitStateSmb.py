from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Permutation.RemapEntity import RemapEntity
from convert.formats.Fusion.BrepCodec.Journal.Planar.MakeLiveTable import MakeLiveTable
from convert.formats.Fusion.BrepCodec.Journal.Writing.EmitWireRecord import (
    EmitWireRecord,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.formats.Fusion.BrepCodec.Wire.EmitBrepHeader import EmitBrepHeader
from convert.formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName
from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode


def EmitStateSmb(Model: JournalModel, StateId: int | None = None) -> bytes:
    Table = MakeLiveTable(Model, StateId)
    Ordinals = {Reference: Index for Index, Reference in enumerate(Table.LiveSlots)}
    Mapping = tuple(Ordinals.get(Reference, -1) for Reference in Table.SlotMap)
    Entities = tuple(Table.Entities[Reference] for Reference in Table.LiveSlots)
    RootCount = 1 + sum(isinstance(Value, BodyNode) for Value in Entities)
    if RootCount < 2:
        raise ValueError("Fusion standalone geometry requires a live body")
    Parts = [EmitBrepHeader(Model.Stamp, RootCount, False, 10.0)]
    for Value in Entities:
        if Value is None:
            raise ValueError("Fusion live state contains an absent revision")
        Parts.append(EmitWireRecord(MakeEntityNode(RemapEntity(Value, Mapping))))
    Parts.append(EncodeSmbName("End-of-ASM-data"))
    Payload = b"".join(Parts)
    if len(Payload) > 2 * 1024 * 1024:
        raise ValueError("Encoded Fusion state exceeds its byte quota")
    return Payload
