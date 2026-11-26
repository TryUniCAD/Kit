from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue


# duplicate native writes need an independent wire key while existing builders retain their field alias
def ReadRuleValue(ScopeValue: FieldScope, RuleValue: NativeField) -> object:
    try:
        return ReadScopeValue(ScopeValue, RuleValue.NameValue)
    except KeyError:
        if not RuleValue.OtherName:
            raise
        return ReadScopeValue(ScopeValue, RuleValue.OtherName)
