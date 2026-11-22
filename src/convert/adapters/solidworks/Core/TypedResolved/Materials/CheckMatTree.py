from convert.adapters.base.SafeParsing import ParseUntrusted
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Core.TypedResolved.Materials.NamedMatRead import (
    NamedMatRead,
)

# the saved material document qualifies its own namespace independently of the archive identity
KMaterialTreeRoot = "{http://www.solidworks.com/sldmaterials}materials"

# the saved part assignment has one specific xml stream owner
KMaterialTree = "swXmlContents/MATERIALTREE"


# the xml configuration and density must corroborate the binary assignment
def CheckMatTree(DataValue: bytes, ReadValue: NamedMatRead) -> None:
    if not DataValue.startswith(b"\xff\xfe"):
        raise BodyUnsupported(
            "SOLIDWORKS MATERIALTREE requires its current UTF-16LE framing"
        )
    try:
        RootValue = ParseUntrusted(DataValue.decode("utf-16"))
        ClassRows = RootValue.findall("classification/material")
        ConfigRows = RootValue.findall("configurationslist/configuration")
        if (
            RootValue.tag != KMaterialTreeRoot
            or tuple(EntryValue.tag for EntryValue in RootValue)
            != ("curves", "classification", "configurationslist")
            or len(ClassRows) != 1
            or len(ConfigRows) != 1
        ):
            raise ValueError("unexpected material directory owners")
        MaterialValue = ClassRows[0]
        ConfigValue = ConfigRows[0]
        PhysicalRows = MaterialValue.findall("physicalproperties")
        DensityRows = MaterialValue.findall("physicalproperties/DENS")
        NameValue = f"{ReadValue.CatalogValue}|{ReadValue.MaterialName}"
        if (
            len(PhysicalRows) != 1
            or len(DensityRows) != 1
            or set(ConfigValue.attrib) != {"name", "material"}
            or len(ConfigValue) != 0
            or MaterialValue.get("name") != NameValue
            or MaterialValue.get("matid") != str(ReadValue.NativeId)
            or ConfigValue.get("material") != f"{NameValue}|{ReadValue.NativeId}"
            or ConfigValue.get("name") != ReadValue.CfgName
            or float(DensityRows[0].attrib["value"]) != ReadValue.DensityValue
        ):
            raise ValueError("material identity, configuration or density differs")
    except (KeyError, SyntaxError, ValueError) as ErrorInfo:
        raise BodyUnsupported(
            "SOLIDWORKS MATERIALTREE does not corroborate its binary assignment"
        ) from ErrorInfo
