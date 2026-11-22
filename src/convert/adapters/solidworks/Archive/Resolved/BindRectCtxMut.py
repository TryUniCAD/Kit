from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.RectDimFields import (
    KRectDimFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the alternate point pair rows extend only the dimensioned rectangle resumption context
KSketchSchema = "sk.sgSketch.FUN_4c5a0f00"


# model only width and height emission adds the actual two point driving dimensions to the common sketch grammar
def BindRectCtxMut(ContextValue: BodyContext) -> None:
    SketchRules = tuple(
        (
            ReplaceValue(RuleValue, BodyValue=(NativeField("Node", "d", "sgValG2Dim"),))
            if RuleValue.NameValue == "val_g2"
            else RuleValue
        )
        for RuleValue in ContextValue.LayoutsValue[KSketchSchema]
    )
    ContextValue.LayoutsValue = (
        dict(ContextValue.LayoutsValue)
        | KRectDimFields
        | {
            KSketchSchema: SketchRules,
        }
    )
    ContextValue.SchemasValue = dict(ContextValue.SchemasValue) | {
        "moDimText_c": (1,),
        "moSkDimHandleValG2_c": (1,),
        "sgPntPntDist": (1,),
    }
