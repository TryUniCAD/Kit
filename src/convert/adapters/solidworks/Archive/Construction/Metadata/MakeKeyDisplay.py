from decimal import Context as DecimalContext, Decimal, ROUND_HALF_UP as HalfUp
from math import degrees as Degrees

from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleNum import (
    ReadStyleNum,
)

# legacy keyword callers retain their own length conversion while measured native displays use document precision
KKeyLengthScale = {"mm": 0.001, "m": 1.0, "in": 0.0254}


# effective keyword names and values come from the parameter while native display settings specify rounding and glyphs
def MakeKeyDisplay(
    NameValue: str,
    ParameterValue: float,
    UnitValue: str,
    *,
    DisplayPlaces: int | None = None,
    GlyphValue: str | None = None,
) -> KeywordDim:
    AngleUnit = "degree" if UnitValue == "degree" else None
    ParameterValue = ReadStyleNum(ParameterValue, "keyword parameter value")
    if DisplayPlaces is None:
        Shown = (
            Degrees(ParameterValue)
            if AngleUnit
            else ParameterValue / KKeyLengthScale[UnitValue]
        )
        return KeywordDim(NameValue, Shown, AngleUnit, GlyphValue)
    if type(DisplayPlaces) is not int or not 0 <= DisplayPlaces <= 16:
        raise ValueError("keyword display precision must be between zero and sixteen")
    if UnitValue not in ("mm", "degree"):
        raise ValueError("fixed native keyword display requires millimetres or degrees")
    Shown = Degrees(ParameterValue) if AngleUnit else ParameterValue * 1000.0
    Fixed, PlacesValue = RoundKeyDisplay(Shown, DisplayPlaces)
    return KeywordDim(NameValue, Fixed, AngleUnit, GlyphValue, PlacesValue)


# native decimal output rounds positive ties upward and omits insignificant fractional zeros
def RoundKeyDisplay(NumberValue: float, PlacesValue: int) -> tuple[float, int]:
    FiniteValue = ReadStyleNum(NumberValue, "converted keyword parameter value")
    ExactValue = Decimal(str(FiniteValue))
    ScaleValue = Decimal((0, (1,), -PlacesValue))
    ContextValue = DecimalContext(
        prec=max(28, ExactValue.adjusted() + PlacesValue + 2), rounding=HalfUp
    )
    TextValue = format(ExactValue.quantize(ScaleValue, context=ContextValue), "f")
    if PlacesValue:
        TextValue = TextValue.rstrip("0").rstrip(".")
    return float(TextValue), len(TextValue.partition(".")[2])
