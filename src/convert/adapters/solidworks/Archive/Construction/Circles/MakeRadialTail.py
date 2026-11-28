from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)


# one ordinary radial leader uses the generated subtype bits and empty additional leader owners
def MakeRadialTail(IsDiameter: bool, IsSolid: bool) -> dict[str, object]:
    FlagsValue = 0x380082 | (0 if IsDiameter else 0x10) | (4 if IsSolid else 0)
    return {
        "ffd8": FlagsValue,
        "ffd4": 0,
        "nfc0": 0,
        "ffc0": (),
        "f1050": None,
        "f1048": "",
        "f1068": None,
        "has_f1060": 0,
        "f1090": None,
        "f10a8": None,
        "f10a4": 0,
        "ffe0": 0.0,
        "ffe8": 0.0,
        "fff0": 0.0,
        "fff8": 0.0,
        "f1000": 0.0,
        "f1008": 0.0,
        "f1010": MakePoint(),
        "f1028": MakePoint(),
    }
