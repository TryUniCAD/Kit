from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode
from convert.adapters.Fusion.Native.Circular.RimPolicy.ReadRimContext import (
    ReadRimContext,
)
from convert.adapters.Fusion.Native.Circular.DualSides.ReadDualLive import ReadDualLive
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Planar.MakeLiveTable import MakeLiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel


# corruption targets are found through source state aliases instead of captured record offsets
def FindRimSlot(Model: DocumentModel, CaseName: str) -> tuple[int, int]:
    Context = ReadRimContext(BuildGraph(Model))
    History = Model.Bodies[0].History
    assert isinstance(History, JournalModel)
    StateId = IntegerValue(
        Context.Feature.Fields[
            "startModelHS" if CaseName == "tracker_owner" else "endModelHS"
        ]
    )
    State = ReadDualLive(History, StateId)
    ClassName = (
        "TorusNode"
        if CaseName.startswith("torus")
        else (
            "EdgeNode"
            if CaseName == "seam_parameter"
            else (
                "TrackAttrib"
                if CaseName == "tracker_owner"
                else (
                    "CoedgeNode"
                    if CaseName == "coedge_partner"
                    else (
                        "TimeAttrib"
                        if CaseName == "body_clock"
                        else (
                            "TagAttrib"
                            if CaseName in ("blend_operation", "attribute_cycle")
                            else (
                                "SketchAttrib"
                                if CaseName == "bottom_source"
                                else "FaceNode"
                            )
                        )
                    )
                )
            )
        )
    )
    for Index, Entity in enumerate(State.Entities):
        if type(Entity).__name__ != ClassName:
            continue
        if isinstance(Entity, FaceNode):
            Surface = State.Entities[Entity.Surface]
            if not isinstance(Surface, PlaneNode) or Surface.OriginCm[2] <= 0:
                continue
        if CaseName == "blend_operation":
            assert isinstance(Entity, TagAttrib)
            Owner = State.Entities[Entity.Links.OwnerRef]
            if not isinstance(Owner, FaceNode) or not isinstance(
                State.Entities[Owner.Surface], TorusNode
            ):
                continue
        Table = MakeLiveTable(History, StateId)
        return (
            Table.Records[sorted(Table.LiveSlots)[Index]],
            sorted(Table.LiveSlots)[Index],
        )
    raise ValueError("Requested live rim record is absent")
