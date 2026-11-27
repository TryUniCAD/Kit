from types import SimpleNamespace
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import BodyFaces,FaceCoedges
from convert.adapters.Fusion.Native.Circular.DualSnapshots.ReadSnapRoles import ReadSnapRoles
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode


def snapshot_tags(state):
    roles=ReadSnapRoles(state);root=next(i for i,role in roles if role=='solid')
    faces=BodyFaces(state,state.Entities[root]);owners={}
    for face in faces:
        index=state.Entities.index(face);surface=state.Entities[face.Surface]
        role='SideFace' if isinstance(surface,ConeNode) else 'BottomFace' if isinstance(surface,PlaneNode) and abs(surface.OriginCm[2])<1e-10 else 'TopFace'
        assert role not in owners;owners[role]=index
        for coedge in FaceCoedges(state,face):
            edge=state.Entities[coedge.EdgeRef];curve=state.Entities[edge.CurveRef];owners['BottomEdge' if abs(curve.OriginCm[2])<1e-10 else 'TopEdge']=coedge.EdgeRef
    tags={}
    for role,index in owners.items():
        attribute,=(e for e in state.Entities if isinstance(e,TagAttrib) and e.Links.OwnerRef==index);tag,=attribute.Groups;tags[role]=tag
    assert set(tags)=={'SideFace','TopFace','BottomFace','TopEdge','BottomEdge'}
    return SimpleNamespace(TagSet=SimpleNamespace(**tags))
