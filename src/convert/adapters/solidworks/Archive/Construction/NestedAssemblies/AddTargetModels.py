from xml.etree.ElementTree import Element, SubElement
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.XmlModelAttrs import (
    XmlModelAttrs,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.XmlNumbers import (
    XmlNumbers,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.XmlRefAttrs import (
    XmlRefAttrs,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.XmlWalkState import (
    XmlWalkState,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# model closure must preserve dependency order actual selected configurations and direct reference targets within the independently computed xml namespace
def AddTargetModels(
    StateValue: XmlWalkState, ModelsValue: Element, RootName: str
) -> None:
    for TargetValue in StateValue.ModelValues:
        IdentityValue = id(TargetValue.RootValue)
        ModelId, FileId = StateValue.NodeIds[IdentityValue]
        Attributes = XmlModelAttrs(
            TargetValue.CurrentConfig,
            ModelId,
            FileId,
            RootName,
            FieldInt(TargetValue.CurrentConfig.FieldsValue, "f860"),
        )
        if TargetValue.RootValue.ClassValue.NameValue == "moAssembly_c":
            Attributes["swBoundingBox"] = XmlNumbers(
                TargetValue.BoundsValue[f"b{IndexValue}"]
                for IndexValue in (6, 7, 8, 3, 4, 5)
            )
            Attributes["swAssemblyFeatureEffectedComponents"] = ""
        ModelValue = SubElement(ModelsValue, "swModel", Attributes)
        for ReferenceId, Reference, ChildId in StateValue.RefValues[IdentityValue]:
            _ = SubElement(
                ModelValue, "swReference", XmlRefAttrs(Reference, ReferenceId, ChildId)
            )
