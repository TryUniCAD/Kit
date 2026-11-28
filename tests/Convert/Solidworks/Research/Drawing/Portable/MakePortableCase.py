from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Drawing.Model.MakeModelInput import (
    MakeModelInput,
)


# independent document sizes text encodings units and presentation must exercise whole file construction beyond one research recipe
def MakeBlankCase(Label: str, Numerator: int, Denominator: int) -> dict[str, object]:
    Request = MakeModelInput(Label, Numerator, Denominator)
    Presentation = CastValue(dict[str, object], Request["presentation"])
    Provenance = CastValue(dict[str, object], Request["provenance"])
    SheetValue = CastValue(dict[str, object], Request["sheet"])
    if Label == "PortableBeta":
        SheetValue["custom_property_view"] = (
            'fresh Ω 文字 "quoted" & <tags> ' + "s" * 360
        )
        Provenance.update(
            author="fresh Ω author",
            company="company & <division>",
            comment="explicit / > marker",
            created_at=1794871004,
            modified_at=1794871209,
        )
    if Label == "PortableGamma":
        SheetValue["length_unit"] = "in"
        CastValue(dict[str, object], Presentation["units"]).update(
            length_unit="in", unit_system="ips", decimal_places=3
        )
        Presentation["auto_dim_text_link"] = False
    if Label == "PortableDelta":
        SheetValue["name"] = 'fresh 文字 & "sheet" <design>'
        CastValue(dict[str, object], Presentation["definition"])[
            "drafting_standard"
        ] = "moISO_c"
        CastValue(dict[str, object], Presentation["styles"]).update(
            font_name="Liberation Sans", language_id=1041
        )
        Presentation.update(language_id=1041, cjk_saved=True)
        Provenance.update(originating_build_code=2026002, license_origin=10)
    return Request
