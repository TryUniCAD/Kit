from convert.adapters.solidworks.Drawing.Metadata.Writing.XmlTextValue import (
    XmlTextValue,
)


# the measured ordinary text profile preserves authored single lines through an xml dom save
def CheckPropText(RawValue: object) -> str:
    TextValue = XmlTextValue(RawValue, False)
    if any(Newline in TextValue for Newline in ("\r", "\n", "\t")):
        raise ValueError("ordinary part properties require single-line text")
    return TextValue
