from pathlib import Path as FilePath
from typing import cast as CastValue

from convert import open_document as OpenDocument


# all native mate roots must resolve actual occurrence and child identities on the normal reader route
def CheckCombinedRead(SourcePath: FilePath, Count: int) -> None:
    Document = OpenDocument(SourcePath, include_brep=False, include_tessellation=False)
    State = CastValue(
        dict[str, object], Document.metadata["solidworks.typed_mates_semantics"]
    )
    assert State["status"] == "admitted" and State["mate_count"] == Count
    Assembly = Document.assembly
    assert Assembly is not None
    assert len(Assembly.mates) == Count and len(Assembly.mate_entities) == 2 * Count
    Identities = {Value.id: Value for Value in Assembly.mate_entities}
    assert len(Identities) == 2 * Count
    for MateValue in Assembly.mates:
        First, Second = (Identities[Value] for Value in MateValue.entity_ids)
        assert First.instance_path != Second.instance_path
        assert First.source_entity_id == Second.source_entity_id
        assert First.source_entity_id is not None
        assert First.source_entity_id.startswith("sldprt:plane:")
        assert First.attributes["typed_archive_selection"] is True
        assert Second.attributes["typed_archive_selection"] is True
