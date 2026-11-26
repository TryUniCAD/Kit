from typing import cast as CastValue


# source diagnostics must distinguish a reader reported direction owner from qualified semantics
def VerifyAxis(
    Source: dict[str, object],
    SourceHash: str,
    Expected: bool,
    OwnerSpan: tuple[int, int, int, int] = (34, 26, 11996, 3037),
) -> None:
    BossId, ProfileId, SpanOffset, SpanLength = OwnerSpan
    Observations = CastValue(list[dict[str, object]], Source["observations"])
    RowsValue = [
        EntryValue
        for EntryValue in Observations
        if EntryValue.get("classification") == "reader_reported_native_direction_owner"
    ]
    assert RowsValue == (
        [
            {
                "classification": "reader_reported_native_direction_owner",
                "path": "/selections/0",
                "source_sha256": SourceHash,
                "selection_id": f"sldprt:selection:{BossId}:axis:{ProfileId}:N_Axis",
                "operation_id": f"sldprt:feature:{BossId}",
                "sketch_owner_id": f"sldprt:feature:{ProfileId}",
                "sketch_id": f"sldprt:sketch:{ProfileId}",
                "support_plane_id": "sldprt:plane:2",
                "provenance_span": {
                    "stream": "Contents/Config-0-ResolvedFeatures",
                    "offset": SpanOffset,
                    "length": SpanLength,
                    "record_kind": "direction-axis",
                },
            }
        ]
        if Expected
        else []
    )
