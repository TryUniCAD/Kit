from typing import cast as CastValue


# source diagnostics must distinguish a reader reported direction owner from qualified semantics
def VerifyAxis(Source: dict[str, object], SourceHash: str, Expected: bool) -> None:
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
                "selection_id": "sldprt:selection:34:axis:26:N_Axis",
                "operation_id": "sldprt:feature:34",
                "sketch_owner_id": "sldprt:feature:26",
                "sketch_id": "sldprt:sketch:26",
                "support_plane_id": "sldprt:plane:2",
                "provenance_span": {
                    "stream": "Contents/Config-0-ResolvedFeatures",
                    "offset": 11996,
                    "length": 3037,
                    "record_kind": "direction-axis",
                },
            }
        ]
        if Expected
        else []
    )
