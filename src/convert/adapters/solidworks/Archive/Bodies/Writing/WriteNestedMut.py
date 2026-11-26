from collections.abc import MutableMapping
from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame


# embedded emission must retain live computed mappings without materializing a second document
def WriteNestedMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    if RuleValue.KindValue == "Base":
        FrameValue.SchemaWriter(FrameValue, RuleValue.NameValue)
        return
    Value = ReadScopeValue(FrameValue.ScopeValue, RuleValue.NameValue)
    if not isinstance(Value, MutableMapping):
        raise ValueError(
            f"SOLIDWORKS embedded body {RuleValue.NameValue} requires fields"
        )
    ScopeValue = FieldScope(
        CastValue(MutableMapping[str, object], Value), FrameValue.ScopeValue
    )
    FrameValue.SchemaWriter(
        ReplaceValue(FrameValue, ScopeValue=ScopeValue), RuleValue.TypeValue
    )
