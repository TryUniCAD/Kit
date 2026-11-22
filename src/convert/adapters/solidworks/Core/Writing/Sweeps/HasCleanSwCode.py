from typing import cast as CastValue


# native status codes are integers and the save flag is its distinct boolean success value
def HasCleanSwCode(Value: object, SaveFlag: bool = False) -> bool:
    if type(Value) is not list:
        return False
    Parts = CastValue(list[object], Value)
    if SaveFlag:
        if not Parts or Parts[0] is not True:
            return False
        Parts = Parts[1:]
    return len(Parts) == 2 and all(
        type(CodeValue) is int and CodeValue == 0 for CodeValue in Parts
    )
