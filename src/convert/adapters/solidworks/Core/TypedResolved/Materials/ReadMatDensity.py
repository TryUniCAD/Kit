from math import isfinite as IsFinite

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Config.Material.CheckMatBody import (
    CheckMatBody,
)
from convert.adapters.solidworks.Archive.Config.Material.MatTypes import (
    KDensityClass,
    KHatchClass,
    KMaterialClass,
    KModelDataClass,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Materials.CheckMatSlots import (
    CheckMatSlots,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# ordinary part density must belong to the real parameter and agree exactly with the active configuration
def ReadMatDensity(PartGraph: ConfigGraph, ConfigValue: ArchiveNode) -> float:
    PartValue = RequireNative(PartGraph.RootValue, "moPart_c")
    PartFields = PartValue.FieldsValue
    HatchValue = RequireNative(PartFields.get("f1418"), KHatchClass.NameValue)
    MaterialValue = RequireNative(PartFields.get("f1420"), KMaterialClass.NameValue)
    DensityNode = RequireNative(
        MaterialValue.FieldsValue.get("f08"), KDensityClass.NameValue
    )
    DataValue = RequireNative(PartFields.get("f1588"), KModelDataClass.NameValue)
    CheckMatSlots(
        PartGraph.MapValue, PartValue, HatchValue, MaterialValue, DensityNode, DataValue
    )
    CheckMatBody(DensityNode)
    CheckMatBody(DataValue)
    Fields = DensityNode.FieldsValue
    DensityValue = Fields.get("f58")
    if (
        not (
            MaterialValue.StartOffset is not None
            and DensityNode.StartOffset is not None
            and DensityNode.StartOffset > MaterialValue.StartOffset
            and MaterialValue.StartOffset == HatchValue.EndOffset
            and DensityNode.EndOffset
            == MaterialValue.EndOffset
            == DataValue.StartOffset
        )
        or PartFields.get("f08") != 0
        or type(DensityValue) is not float
        or not IsFinite(DensityValue)
        or DensityValue <= 0.0
        or Fields.get("f68") != 0
        or "f60" in Fields
        or ConfigValue.FieldsValue.get("fc50") != DensityValue
    ):
        raise BodyUnsupported(
            "SOLIDWORKS assigned material density is absent, overridden or inconsistent"
        )
    return DensityValue
