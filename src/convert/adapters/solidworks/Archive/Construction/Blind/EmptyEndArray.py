# constructor collections derive their count from the actual fresh row list rather than saved framing
def EmptyEndArray() -> dict[str, object]:
    RowsValue: list[dict[str, object]] = []
    return {"n": len(RowsValue), "items": RowsValue}
