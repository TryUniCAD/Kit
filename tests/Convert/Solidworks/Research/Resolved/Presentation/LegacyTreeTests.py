from collections.abc import Mapping
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Resolved.RunPublicRead import RunPublicRead


# the current ordinary presentation profile must preserve older native documents through their established public reader path
def TestOlderTree() -> None:
    Document = RunPublicRead(
        KRepoRoot / "re/solidworks/examples/.SLDPRT/example.SLDPRT"
    )
    Evidence = CastValue(
        Mapping[str, object], Document.metadata["solidworks.typed_resolved_semantics"]
    )
    assert Evidence["status"] == "unsupported"
    assert Evidence["archive_version"] == 18000 and "native_tree" not in Evidence
    assert len(Document.feature_timeline) == 39
    assert all(
        not Feature.attributes["typed_archive_owner"]
        for Feature in Document.feature_timeline
    )
