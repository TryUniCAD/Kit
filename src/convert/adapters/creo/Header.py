from __future__ import annotations

from dataclasses import dataclass

from convert.adapters.creo.CreoFormat import CreoFormat


@dataclass(frozen=True, slots=True)
class CreoHeader:
    kind: str
    base: int
    version_line: str
    model_name: str
    common_name: str
    product_version: str
    header_lines: tuple[str, ...]


def GetKind(LineText: str) -> str:
    Words = LineText.rstrip("\\").split()
    if len(Words) < 2 or Words[0] != "#UGC:2":
        raise CreoFormat("Creo header must start with #UGC:2")
    KindText = Words[1]
    if KindText == "ASSEMBLY":
        raise CreoFormat(
            "Creo assemblies are not supported by the part-only creo.prt adapter"
        )
    if KindText not in {"PART", "PART/SHEETMETAL"}:
        raise CreoFormat(f"unsupported Creo model kind {KindText!r}")
    return KindText


def GetBase(LineText: str) -> int:
    Words = LineText.rstrip("\\").split()
    if len(Words) < 3:
        raise CreoFormat("Creo header must declare the section base")
    BaseText = Words[-1]
    try:
        BaseValue = int(BaseText, 16)
    except ValueError as ErrorInfo:
        raise CreoFormat("Creo section base is not hexadecimal") from ErrorInfo
    return BaseValue


def GetCommonName(Lines: tuple[str, ...]) -> str:
    Names: list[str] = []
    for LineText in Lines:
        Prefix = "#- CMNM "
        if not LineText.startswith(Prefix):
            continue
        Payload = LineText[len(Prefix) :]
        if len(Payload) < 3:
            continue
        CountText = Payload[:3]
        try:
            NameSize = int(CountText, 16)
        except ValueError:
            continue
        NameBytes = Payload[3:].encode("latin-1")[:NameSize]
        NameText = NameBytes.decode("latin-1").rstrip(" ")
        if NameText:
            Names.append(NameText)
    if len(set(Names)) != 1:
        return ""
    return Names[0]


def GetProductVersion(Text: str) -> str:
    Markers = ("Version ", "Release ", "Release")
    for Marker in Markers:
        Start = Text.find(Marker)
        if Start < 0:
            continue
        Tail = Text[Start + len(Marker) :].strip()
        if not Tail:
            continue
        return Tail.split()[0].rstrip(",")
    return ""


def ReadHeader(DataValue: bytes) -> CreoHeader:
    Marker = b"#-END_OF_UGC_HEADER\n"
    EndIndex = DataValue.find(Marker)
    if EndIndex < 0:
        raise CreoFormat("Creo header lacks its end marker")
    HeaderBytes = DataValue[:EndIndex]
    HeaderText = HeaderBytes.decode("latin-1")
    Lines = tuple(HeaderText.splitlines())
    if not Lines:
        raise CreoFormat("Creo header is empty")
    FirstLine = Lines[0]
    KindText = GetKind(FirstLine)
    BaseValue = GetBase(FirstLine)
    ExpectedBase = EndIndex + len(Marker)
    if BaseValue != ExpectedBase:
        raise CreoFormat("Creo section base does not follow the header")
    TailIndex = DataValue.find(b"#UGC_TOC", BaseValue)
    if TailIndex < 0:
        TailIndex = len(DataValue)
    BannerBytes = DataValue[BaseValue:TailIndex]
    BannerText = BannerBytes.decode("latin-1")
    BannerLines = tuple(BannerText.splitlines())
    VersionLine = next(
        (
            LineText
            for LineText in BannerLines
            if LineText.startswith("#Creo") or LineText.startswith("#Pro/ENGINEER")
        ),
        "",
    )
    CommonName = GetCommonName(Lines)
    ModelName = CommonName
    ProductVersion = GetProductVersion(VersionLine)
    return CreoHeader(
        kind=KindText,
        base=BaseValue,
        version_line=VersionLine,
        model_name=ModelName,
        common_name=CommonName,
        product_version=ProductVersion,
        header_lines=Lines,
    )
