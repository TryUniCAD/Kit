import json as JsonTools

from Budget.TrimPatches import TrimPatches


# reclaim duplicate diff text before rejecting any immutable source snapshot for capacity
def AddSourceMut(
    Context: dict[str, object],
    Source: dict[str, object],
    Sources: list[dict[str, object]],
) -> None:
    Sources.append(Source)
    if len(JsonTools.dumps(Context).encode()) <= 900000:
        return
    Sources[:] = TrimPatches(Sources)
    if len(JsonTools.dumps(Context).encode()) > 900000:
        Sources[-1].update(
            {
                "before": None,
                "after": None,
                "target": None,
                "patch": None,
                "omitted": "Complete source exceeds the review context budget",
            }
        )
