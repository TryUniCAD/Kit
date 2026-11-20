from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.LightPropFields import (
    KLightPropFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# shared light order carries independent scalar occurrences for exact typed inspection
KLightBaseFields = (
    NativeField("Base", "moModelFeature_c"),
    NativeField("Scalar", "f390", "f64"),
    NativeField("Scalar", "f398", "f64"),
    NativeField("Scalar", "f3a0", "f64"),
    NativeField("Scalar", "f3a8", "u32"),
    NativeField("Boolean", "state", "i32"),
    NativeField("Scalar", "f428", "i32"),
    NativeField("Normalize", "f36c", "i32", ModeValue="Zero"),
    NativeField("Scalar", "f4f0", "i32"),
    NativeField("Text", "f4f8"),
    NativeField("Scalar", "f384#0", "i32", OtherName="f384"),
    NativeField("Scalar", "f388", "i32"),
    NativeField("Scalar", "f384", "i32"),
    NativeField("Scalar", "f478", "f64"),
    NativeField("Scalar", "f488", "i32"),
    NativeField("Scalar", "f490", "f64"),
    NativeField("Embed", "f500", "moUserProperty_c.restore"),
)

# the scene owner and both concrete lights share their measured feature base and name graph
KLightFields = MappingProxyType(
    {
        "moEnvFolder_c": (NativeField("Base", "moFolder_c"),),
        "moAmbientLight_c": (NativeField("Base", "moLightFeature_c.FUN_4bc0b030"),),
        "moDirectionLight_c": (
            NativeField("Base", "moLightFeature_c.FUN_4bc0b030"),
            NativeField("Embed", "f3b0", "mgVector_c.restore"),
            NativeField("Scalar", "f498", "f64"),
        ),
        "moFolder_c": (
            NativeField("Base", "moFeature_c"),
            NativeField("Scalar", "f360", "i32"),
            NativeField("Scalar", "f370", "i32"),
        ),
        "moModelFeature_c": (
            NativeField("Base", "moFeature_c"),
            NativeField("Base", "moFeature_c.FUN_4bb2b240"),
            NativeField("Scalar", "f35c", "i32"),
        ),
        "moFeature_c.FUN_4bb2b240": (),
        "moNodeName_c": (NativeField("Text", "f08"),),
        "moLightFeature_c.FUN_4bc0b030": KLightBaseFields,
        "moUserProperty_c.restore": KLightPropFields,
    }
)
