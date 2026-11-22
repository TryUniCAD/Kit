from types import MappingProxyType

# source free assembly save preferences require an explicit target policy rather than captured application state
KAsmSavePolicy = MappingProxyType(
    {
        "5fc": False,
        "5fd": 0.0,
        "5fe": False,
        "5ff": 0.0,
        "600": False,
        "601": True,
        "602": True,
        "603": True,
        "604": True,
        "605": 0,
    }
)
