from typing import cast as CastValue

from interchange import CadDocument, MateEntityKind
from tests.Convert.Solidworks.Research.Assembly.PlanarMateInput import KMateLength


# the public relationship must retain ordered real occurrences and a plane actually present in its child document
def AssertPublic(Document: CadDocument) -> None:
    Document.assert_valid()
    assert Document.assembly is not None
    Assembly = Document.assembly
    assert len(Assembly.mates) == 1 and len(Assembly.mate_entities) == 2
    MateValue = Assembly.mates[0]
    assert MateValue.name == "ProjectedDistance" and str(MateValue.kind) == "distance"
    assert MateValue.value is not None and MateValue.value.value == KMateLength * 1000
    Report = CastValue(
        dict[str, object], Document.metadata["solidworks.typed_mates_semantics"]
    )
    assert Report["status"] == "admitted" and Report["full_selected_mate_graph"] is True
    assert Report["public_writer_qualified"] is False
    First, Second = Assembly.mate_entities
    assert First.kind == Second.kind == MateEntityKind.PLANE
    assert First.instance_path != Second.instance_path
    InstanceMap = {Value.id: Value for Value in Assembly.instances}
    assert [
        InstanceMap[Value.instance_path[0]].reference_number
        for Value in (First, Second)
    ] == ["2", "1"]
    Child = Assembly.documents[0].document
    RightPlane = next(
        Value for Value in Child.support_planes if Value.name == "Right Plane"
    )
    assert First.source_entity_id == Second.source_entity_id == RightPlane.id
    assert MateValue.entity_ids == (First.id, Second.id)
    assert len({Value.id for Value in (*Assembly.mates, *Assembly.mate_entities)}) == 3
