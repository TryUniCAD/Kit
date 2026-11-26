# constructor collections require actual typed list owners even when their independently computed element count is zero
def MakeObList() -> dict[str, object]:
    return {"n": 0, "items": []}
