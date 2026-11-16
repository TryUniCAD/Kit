from __future__ import annotations

from typing import cast as CastValue


# retained provenance must resolve every field back to its document and owning object
def AssertContext(
    Context: object,
    Nodes: dict[str, dict[str, object]],
    Streams: dict[str, dict[str, object]],
) -> None:
    assert isinstance(Context, dict)
    ContextData = CastValue(dict[str, object], Context)
    assert set(ContextData) == {"stream", "path", "owner_object"}
    assert ContextData["stream"] in Streams
    assert isinstance(ContextData["path"], list)
    for PathPart in CastValue(list[object], ContextData["path"]):
        assert type(PathPart) in {str, int}
    OwnerId = ContextData["owner_object"]
    if OwnerId is not None:
        assert isinstance(OwnerId, str)
        assert Nodes[OwnerId]["type"] == "object"
