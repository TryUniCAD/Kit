from pathlib import Path as FilePath
from typing import cast as CastValue

from convert import open_document as OpenDocument


# normal sdk metadata must use the complete graph codec while preserving its legacy feature reader
def AssertCfgRead(InputPath: FilePath) -> None:
    Document = OpenDocument(InputPath, include_brep=False, include_tessellation=False)
    InfoValue = CastValue(
        dict[str, object], Document.metadata["solidworks.typed_configuration_graph"]
    )
    assert InfoValue["status"] == "complete" and InfoValue["archive_version"] == 19000
    assert (
        InfoValue["model_class"] == "moPart_c"
        and InfoValue["full_linked_graph"] is False
    )
    assert InfoValue["resolved_body_codec_promoted"] is False
    UsageValue = CastValue(dict[str, object], InfoValue["usage"])
    assert UsageValue["completed"] is True and UsageValue["used_schemas"]
    ContextValue = CastValue(dict[str, object], InfoValue["resolved_dependency"])
    assert ContextValue["manager_context_available"] is True
    assert ContextValue["manager_map_seeded_configuration"] is False
    assert Document.sketches and Document.feature_timeline
