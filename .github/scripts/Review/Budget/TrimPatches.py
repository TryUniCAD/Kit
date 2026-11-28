# complete before and after snapshots make a patch redundant rather than missing source
def TrimPatches(Sources: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        (
            {**Source, "patch": None}
            if "omitted" not in Source
            and isinstance(Source.get("before"), str)
            and isinstance(Source.get("after"), str)
            else Source
        )
        for Source in Sources
    ]
