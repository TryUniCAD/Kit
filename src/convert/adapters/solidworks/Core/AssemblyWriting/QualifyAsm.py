from dataclasses import replace as ReplaceValue

from convert.adapters.base.WriteResult import WriteResult


# the normal writer reports the independently measured profile without altering generated assembly bytes
def QualifyAsm(ResultValue: WriteResult, IsPerpendicular: bool) -> WriteResult:
    ProfileValue = (
        "2026_ordinary_owned_perpendicular_assembly"
        if IsPerpendicular
        else "2026_ordinary_owned_planar_assembly"
    )
    return ReplaceValue(
        ResultValue,
        application_usable=True,
        vendor_loadable=True,
        metadata={
            **ResultValue.metadata,
            "native_qualification": ProfileValue,
            "output_scope": "one_assembly_and_one_owned_part",
            "overwrite_supported": False,
        },
    )
