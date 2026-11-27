from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import FaceCoedges


def recipe_witness(state,roles,source):
    recipe=source['recipe'];payload=recipe.Payload;edge_index=source['selected_edge'];edge=state.Entities[edge_index]
    assert isinstance(edge,EdgeNode) and edge_index==roles['edges']['top'] and edge.StartVertex==edge.EndVertex
    def tag(index):
        saved,=recipe.Tags[index]
        return FeatureTag(''.join(map(chr,saved.PrimaryId)),saved.OperationIds,saved.SecondaryId,saved.ApproachId)
    def owner(index,kind):
        found,=(a.Links.OwnerRef for a in state.Entities if isinstance(a,TagAttrib) and a.Groups==(tag(index),))
        assert isinstance(state.Entities[found],kind);return found
    assert owner(payload.PrimaryTagIndex,EdgeNode)==edge_index
    adjacent={owner(face.PrimaryTagIndex,FaceNode) for face in payload.AdjacentFaces}
    assert adjacent=={roles['faces']['side'],roles['faces']['top']} and len(payload.AdjacentFaces)==2
    physical={i for i,face in enumerate(state.Entities) if isinstance(face,FaceNode) and any(c.EdgeRef==edge_index for c in FaceCoedges(state,face))}
    assert physical==adjacent
    vertex,=payload.AdjacentVertices;assert vertex.PrimaryTagIndex==-1
    assert {owner(face.PrimaryTagIndex,FaceNode) for face in vertex.AdjacentFaces}==adjacent and len(vertex.AdjacentFaces)==2
    only,=vertex.AdjacentEdges;assert owner(only.PrimaryTagIndex,EdgeNode)==edge_index and not only.AdjacentFaces and not only.AdjacentVertices
    used={payload.PrimaryTagIndex,*[face.PrimaryTagIndex for face in payload.AdjacentFaces],*[face.PrimaryTagIndex for face in vertex.AdjacentFaces],only.PrimaryTagIndex}
    assert used==set(range(len(recipe.Tags)))
    return dict(selected_edge=edge_index,adjacent_faces=sorted(adjacent),seam_vertex=edge.StartVertex,full_tag_groups=len(used))
