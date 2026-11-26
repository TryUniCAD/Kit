# constructor collections need independent payloads and lengths derived from their actual rows
def EmptyRootRows() -> dict[str, object]:
    ItemsValue: tuple[object, ...] = ()
    return {"n": len(ItemsValue), "items": ItemsValue}
