from collections.abc import Callable
from dataclasses import fields as DataclassFields
from typing import (
    TYPE_CHECKING as TypeChecking,
    cast as CastValue,
    get_type_hints as TypeHints,
)

if TypeChecking:
    from _typeshed import DataclassInstance

from convert.adapters.solidworks.Core.DrawingWriting.Rewrite.BlankOwnerCtor import (
    BlankOwnerCtor,
)
from interchange.serialization.OptionalFields import KOmitNullField


# only complete official dataclass fields may recreate native intent without dropping unknown semantic state
def ReadBlankOwner(
    TypeValue: type,
    Value: object,
    ReadValue: Callable[[object, object], object],
) -> object:
    if type(Value) is not dict:
        raise ValueError("blank metadata owner has no complete field mapping")
    Fields = CastValue(dict[str, object], Value)
    Hints = CastValue(dict[str, object], TypeHints(TypeValue))
    DataFields = DataclassFields(CastValue("DataclassInstance", TypeValue))
    Schema = {FieldValue.name: Hints[FieldValue.name] for FieldValue in DataFields}
    Omitted = {
        FieldValue.name
        for FieldValue in DataFields
        if FieldValue.default is None and FieldValue.metadata.get(KOmitNullField)
    }
    if set(Fields) - Schema.keys() or Schema.keys() - Fields.keys() - Omitted:
        raise ValueError("blank metadata owner has unknown or missing fields")
    Constructor = CastValue(BlankOwnerCtor, TypeValue)
    return Constructor(
        **{
            NameValue: ReadValue(Schema[NameValue], Fields[NameValue])
            for NameValue in Fields
        }
    )
