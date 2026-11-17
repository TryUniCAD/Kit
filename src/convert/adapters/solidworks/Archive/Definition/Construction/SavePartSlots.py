from types import MappingProxyType

# ordinary save-as-part settings expose the exact native preferences without assuming their names
KSavePartSlots = MappingProxyType(
    {
        "5fc": "f0c",
        "5fd": "f10",
        "5fe": "f18",
        "5ff": "f20",
        "600": "f28",
        "601": "f30",
        "602": "f34",
        "603": "f2c",
        "604": "f38",
        "605": "f3c",
    }
)
