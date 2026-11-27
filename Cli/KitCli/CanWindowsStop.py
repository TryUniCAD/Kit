from ast import Assign as AstAssign, Constant as AstConst, Name as AstName
from ast import parse as ParseAst
from pathlib import Path as FilePath


# older trusted supervisors must reject console cancellation before they can claim durable jobs
def CanWindowsStop(ScriptPath: FilePath) -> bool:
    with ScriptPath.open("rb") as Source:
        Content = Source.read(1024 * 1024 + 1)
    if len(Content) > 1024 * 1024:
        raise ValueError("Selected supervisor exceeds the capability inspection limit")
    try:
        SyntaxTree = ParseAst(Content, filename=str(ScriptPath))
    except SyntaxError as Error:
        raise ValueError("Selected supervisor has invalid Python syntax") from Error
    Markers = [
        Element.value
        for Element in SyntaxTree.body
        if isinstance(Element, AstAssign)
        and len(Element.targets) == 1
        and isinstance(Element.targets[0], AstName)
        and Element.targets[0].id == "KWindowsCliProtocol"
    ]
    return (
        len(Markers) == 1
        and isinstance(Markers[0], AstConst)
        and type(Markers[0].value) is int
        and Markers[0].value == 1
    )
