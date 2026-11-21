from convert.adapters.solidworks.Archive.Definition.Construction.MakeDocOptions import (
    MakeDocOptions,
)


# ordinary fresh ui options derive all empty collections and preserve nested ownership
def MakeDefTail() -> dict[str, object]:
    return {
        "f1138": "",
        "f1158": {"items": []},
        "f1150": "",
        "ff40": {"items": []},
        "f1140": "",
        "ff88": {"items": []},
        "ffb0": {"items": []},
        "f1348": 0,
        "f1350": 0,
        "f134c": 0,
        "f1354": 0,
        "fa78": 0,
        "f1358": 0,
        "f1370": MakeDocOptions(),
        "f1388": 1,
        "f1390": 1,
        "f7bc": 0,
        "f135c": 1,
        "f13c8": 0,
        "f13d0": {"items": []},
        "f1400": 1,
        "f1408": 1,
        "f13f0": 0,
        "fa7c": 0,
        "fa80": 0,
        "fd78": 2,
        "f12e8": None,
        "f1424": 0,
        "f930": 0,
        "f1304": 0,
        "fd7c": 3,
        "f1368": 1,
        "f3e8": 0,
        "f11a0": [],
    }
