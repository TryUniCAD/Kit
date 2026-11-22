from re import compile as CompilePattern

# a namespace qualified local name excludes the colon from the xml fifth edition name grammar
KNameStart = (
    r"A-Z_a-z"
    r"\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF"
    r"\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF"
    r"\uF900-\uFDCF\uFDF0-\uFFFD\U00010000-\U000EFFFF"
)

# a local name tail can also contain the productions additional name characters
KNameTail = KNameStart + r".0-9\u00B7\u0300-\u036F\u203F-\u2040-"

# a single compiled name grammar validates qualified attribute values as character data
KNcName = CompilePattern(f"[{KNameStart}][{KNameTail}]*")


# a qualified attribute value follows the full lexical name grammar before namespace resolution
def IsXmlNcName(NameValue: str) -> bool:
    return KNcName.fullmatch(NameValue) is not None
