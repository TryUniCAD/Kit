from collections.abc import Mapping


# concrete ordinary mate classes must follow authored semantics without treating every additional kind as parallel
def ReadMateClass(KindValue: str) -> str:
    ClassesValue: Mapping[str, str] = {
        "coincident": "moMateCoincident",
        "parallel": "moMateParallel",
        "perpendicular": "moMatePerpendicular",
    }
    if KindValue not in ClassesValue:
        raise ValueError("ordinary nondimensional mate kind is unsupported")
    return ClassesValue[KindValue]
