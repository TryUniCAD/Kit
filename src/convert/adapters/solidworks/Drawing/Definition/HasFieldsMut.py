from convert.adapters.solidworks.Drawing.Definition.FieldScope import FieldScope
from convert.adapters.solidworks.Drawing.Definition.ReadOneField import ReadOneField
from convert.adapters.solidworks.Drawing.Definition.ReadRuleExpr import ReadRuleExpr
from convert.adapters.solidworks.Drawing.Definition.ClauseTypes import KRuleShape


# field statements consume bytes while branch statements retain the same scope
def HasFieldsMut(Scope: FieldScope, Statement: KRuleShape) -> bool:
    match Statement:
        case ("fixed_bytes", str(FieldName), int(WidthValue)):
            Scope.Fields[FieldName] = Scope.Reader.Cursor.TakeBytes(WidthValue)
        case ("normalize", str(FieldName), str(KindName), Expression):
            WireValue = ReadOneField(Scope, KindName)
            if not isinstance(WireValue, (int, float)):
                raise ValueError("drawing normalization requires a scalar")
            Scope.Fields[FieldName] = ReadRuleExpr(Expression, Scope, WireValue)
        case (str(KindName), str(FieldNames)) if KindName in {
            "object",
            "text",
            "count",
            "u8",
            "i8",
            "u16",
            "i16",
            "u32",
            "i32",
            "u64",
            "i64",
            "f32",
            "f64",
        }:
            for FieldName in FieldNames.split():
                Scope.Fields[FieldName] = ReadOneField(Scope, KindName)
        case _:
            return False
    return True
