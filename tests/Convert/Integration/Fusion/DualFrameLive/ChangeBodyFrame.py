from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Planar.MakeLiveTable import MakeLiveTable
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel


# the saved current placement is corrupted by live identity ownership rather than an assumed archive offset
def ChangeBodyFrame(Model: DocumentModel) -> DocumentModel:
    Context = SelectExtrusion(BuildGraph(Model))
    BodyValue = Model.Bodies[0]
    History = BodyValue.History
    assert isinstance(History, JournalModel)
    Table = MakeLiveTable(History, IntegerValue(Context.Extrude.Fields["endModelHS"]))
    Targets = tuple(
        Index
        for Stable in Table.LiveSlots
        for Index in (Table.Records[Stable],)
        if isinstance(History.Entities[Index], TransformNode)
    )
    assert len(Targets) == 1
    Entity = History.Entities[Targets[0]]
    assert isinstance(Entity, TransformNode)
    Entities = tuple(
        ReplaceData(Entity, ScaleFactor=2.0) if Index == Targets[0] else Value
        for Index, Value in enumerate(History.Entities)
    )
    return ReplaceData(
        Model,
        Bodies=(
            ReplaceData(BodyValue, History=ReplaceData(History, Entities=Entities)),
        ),
    )
