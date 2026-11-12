import runpy
from pathlib import Path


RANGES = {
    "Libraries/libadskassetapi_new-16.dylib": [
        ("GeneralLibrary::writePropertyGroupToDataStore_ definition group", 0xc89dc, 0xc8bbc),
        ("GeneralLibrary::writePropertyGroupToDataStore_ instance header", 0xc8bbc, 0xc8de8),
        ("GeneralLibrary::writePropertyGroupToDataStore_ instance values", 0xc8de8, 0xc908c),
        ("GeneralLibrary::writeConnectedAsset_", 0xd20a4, 0xd2200),
        ("GeneralLibrary::loadConnectedAsset_", 0xc860c, 0xc89dc),
        ("PropertyBase::IsConnectionEnabled", 0x13d500, 0x13d508),
        ("PropertyGroup::begin", 0x138be8, 0x138c34),
        ("isDeprecatedProperty", 0x1580e0, 0x1581ec),
        ("deprecated property constants initialization", 0x15c6b0, 0x15c734),
    ],
    "Libraries/libxirangall-16.dylib": [
        ("PrimitiveMethods<UnitsValue>::deserialize and serialize", 0x2a344, 0x2a3ec),
        ("PrimitiveMethods<Color4>::serialize", 0x29f20, 0x29f64),
        ("PrimitiveMethods<string>::serialize", 0x28c10, 0x28c58),
    ],
}


if __name__ == "__main__":
    helper = runpy.run_path(str(Path(__file__).resolve().parents[1] / "DocumentEnvelope" / "InspectEnvelopeNative.py"))
    helper["RANGES"].clear()
    helper["RANGES"].update(RANGES)
    helper["main"]()
