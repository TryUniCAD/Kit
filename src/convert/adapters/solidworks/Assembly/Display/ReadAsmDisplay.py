from xml.etree.ElementTree import Element

from convert.adapters.solidworks.Assembly.Display.CheckDisplay import CheckDisplay
from convert.adapters.solidworks.Assembly.Display.DisplayOwner import DisplayOwner
from convert.adapters.solidworks.Assembly.Display.ReadDisplayXml import (
    KDisplayNs,
    ReadDisplayXml,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive


# unsupported visibility graphs must keep the existing raw assembly reader available
def ReadAsmDisplay(Archive: SldprtArchive, RootValue: Element) -> DisplayOwner | None:
    if RootValue.find(".//sw:swDisplayStateList", KDisplayNs) is None:
        return None
    try:
        DisplayValue = ReadDisplayXml(RootValue)
        CheckDisplay(Archive, DisplayValue)
    except (ValueError, TypeError, KeyError):
        return None
    return DisplayValue
