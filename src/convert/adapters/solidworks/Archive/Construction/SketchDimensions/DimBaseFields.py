# local sketch relations and drivers share the native dimension constructor before their concrete geometry fields are supplied
def DimBaseFields() -> dict[str, object]:
    return {
        "refcount": 0,
        "f28": None,
        "f48": None,
        "f50": -1,
        "f30": 0,
        "f54": 0,
        "f5c": 0,
        "f60": None,
        "f68": 0,
        "has_f78": 0,
    }
