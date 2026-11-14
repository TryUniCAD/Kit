from __future__ import annotations

import ast as AstLib
import re as Regex

from tools.Donors.ReplayRules import KKindPattern


def IsIntValue(AstNode: AstLib.expr) -> bool:
    return (
        isinstance(AstNode, AstLib.Constant)
        and isinstance(AstNode.value, int)
        and not isinstance(AstNode.value, bool)
    )


def IsFieldOp(AstNode: AstLib.AST) -> bool:
    if not isinstance(AstNode, AstLib.Tuple) or len(AstNode.elts) < 4:
        return False
    KindNode = AstNode.elts[3]
    return (
        IsIntValue(AstNode.elts[0])
        and IsIntValue(AstNode.elts[1])
        and isinstance(KindNode, AstLib.Constant)
        and isinstance(KindNode.value, str)
        and Regex.fullmatch(KKindPattern, KindNode.value) is not None
    )
