# an unpopulated body or face property manager needs complete empty framing without invented geometry
def EmptyBodyProps(IsBody: bool) -> dict[str, object]:
    ItemsValue: tuple[object, ...] = ()
    return {
        "n08": len(ItemsValue),
        "bodies" if IsBody else "faces": ItemsValue,
        "n58": len(ItemsValue),
        "props": (),
    }
