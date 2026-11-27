from tests.Convert.Integration.Fusion.RimFillet.Geometry.ChangeRimAttr import (
    ChangeRimAttr,
)
from dataclasses import replace as ReplaceData

from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.Formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib


# typed native corruption changes actual solved fields before the complete archive writer runs
def ChangeRimNode(
    Entity: KJournalEntity, CaseName: str, ReferenceId: int
) -> KJournalEntity:
    if isinstance(Entity, TorusNode):
        if CaseName == "torus_major":
            return ReplaceData(Entity, MajorRadiusCm=Entity.MajorRadiusCm * 1.01)
        if CaseName == "torus_minor":
            return ReplaceData(Entity, MinorRadiusCm=Entity.MinorRadiusCm * 1.1)
        if CaseName == "torus_center":
            return ReplaceData(Entity, CenterCm=(0.0, 0.0, Entity.CenterCm[2] + 0.01))
    if isinstance(Entity, EdgeNode) and CaseName == "seam_parameter":
        return ReplaceData(Entity, StartParam=Entity.StartParam * 0.9)
    if isinstance(Entity, FaceNode) and CaseName == "top_winding":
        return ReplaceData(Entity, Reversed=not Entity.Reversed)
    if isinstance(Entity, TrackAttrib) and CaseName == "tracker_owner":
        return ReplaceData(Entity, TrackedId=Entity.TrackedId + 1)
    if isinstance(Entity, CoedgeNode) and CaseName == "coedge_partner":
        return ReplaceData(Entity, Partner=-1)
    return ChangeRimAttr(Entity, CaseName, ReferenceId)
