from __future__ import annotations

from builtins import getattr as GetAttr
from types import ModuleType


# native archive tags must resolve generated owner identities consistently across separate readers and writers
def RoundTrip(
    ConfigValue: object,
    FileValue: dict[str, object],
    CoreModule: ModuleType,
    RegistryValue: object,
) -> tuple[object, object, object, bytes]:
    OwnerValue = GetAttr(ConfigValue, "f")["owner"]
    SeedValue = GetAttr(CoreModule, "ArchiveMap")(2, {1: ("obj", OwnerValue)})
    StoreValue = GetAttr(CoreModule, "Store")(2, RegistryValue, 19000, seed=SeedValue)
    StoreValue.obj(ConfigValue)
    StoreValue.obj(GetAttr(CoreModule, "Obj")("moSharedFileDef_c", FileValue))
    BlobValue = bytes(StoreValue.out)
    LoadedOwner = GetAttr(CoreModule, "Obj")("moAssembly_c")
    LoadSeed = GetAttr(CoreModule, "ArchiveMap")(2, {1: ("obj", LoadedOwner)})
    LoadValue = GetAttr(CoreModule, "Load")(
        BlobValue, 2, RegistryValue, 19000, seed=LoadSeed
    )
    LoadedConfig, LoadedFile = LoadValue.obj(), LoadValue.obj()
    assert LoadValue.left() == 0
    Rewriter = GetAttr(CoreModule, "Store")(2, RegistryValue, 19000, seed=LoadSeed)
    Rewriter.obj(LoadedConfig)
    Rewriter.obj(LoadedFile)
    assert bytes(Rewriter.out) == BlobValue
    return LoadedConfig, LoadedFile, LoadedOwner, BlobValue
