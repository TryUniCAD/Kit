# part configuration body state must begin with independent empty native lists and explicit absent cache selectors
def PartCfgObject() -> dict[str, object]:
    FieldsValue: dict[str, object] = {
        NameValue: None for NameValue in ("fb0", "fb8", "fa0", "f88", "fa8")
    }
    FieldsValue.update(
        {
            NameValue: {"n": 0, "items": []}
            for NameValue in ("f10", "f60", "f100", "f80", "f68", "f58", "f78", "f70")
        }
    )
    FieldsValue.update(
        dict.fromkeys(
            ("has_c8", "has_d0", "has_e0", "has_e8", "has_f0", "has_98", "fd8", "ff8"),
            0,
        )
    )
    FieldsValue.update({"f0c": 1, "f08": -1})
    return FieldsValue
