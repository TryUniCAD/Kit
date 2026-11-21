from typing import TypeGuard as TypeCheck


# decoded records have interface fields only when the json value is an object
def IsJsonRecord(Value: object) -> TypeCheck[dict[str, object]]:
    return isinstance(Value, dict)


# a typed sequence keeps untrusted decoded entries behind the terminal record check
def IsJsonItems(Value: object) -> TypeCheck[list[object]]:
    return isinstance(Value, list)
