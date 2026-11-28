# fresh manager collections need derived lengths and independent storage instead of shared mutable constructor payloads
def EmptySketchRows(PairsValue: tuple[tuple[str, str], ...]) -> dict[str, object]:
    FieldsValue: dict[str, object] = {}
    for CountName, ArrayName in PairsValue:
        ItemsValue: tuple[object, ...] = ()
        FieldsValue[ArrayName] = ItemsValue
        FieldsValue[CountName] = len(ItemsValue)
    return FieldsValue
