from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope


# nested records must resolve native shared fields through their actual parent scope
def ReadScopeValue(ScopeValue: FieldScope, FieldName: str) -> object:
    Current = ScopeValue
    while True:
        if FieldName in Current.ValuesValue:
            return Current.ValuesValue[FieldName]
        if FieldName in Current.FieldsValue:
            return Current.FieldsValue[FieldName]
        if Current.ParentValue is None:
            raise KeyError(FieldName)
        Current = Current.ParentValue
