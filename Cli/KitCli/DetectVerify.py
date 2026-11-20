from pathlib import Path as FilePath
from ast import (
    Attribute as AstAttr,
    Call as AstCall,
    Constant as AstConst,
    parse as ParseAst,
    walk as WalkAst,
)


# trusted historical checkouts must decode before unsupported verification flags can reject their inputs
def CanNativeVerify(ScriptPath: FilePath) -> bool:
    with ScriptPath.open("rb") as Source:
        Content = Source.read(1024 * 1024 + 1)
    if len(Content) > 1024 * 1024:
        raise ValueError("Selected reader exceeds the capability inspection limit")
    try:
        SyntaxTree = ParseAst(Content, filename=str(ScriptPath))
    except SyntaxError as Error:
        raise ValueError(
            "Selected research reader has invalid Python syntax"
        ) from Error
    return any(
        isinstance(Element, AstCall)
        and isinstance(Element.func, AstAttr)
        and Element.func.attr == "add_argument"
        and any(
            isinstance(Value, AstConst) and Value.value == "--native-verify"
            for Value in Element.args
        )
        for Element in WalkAst(SyntaxTree)
    )
