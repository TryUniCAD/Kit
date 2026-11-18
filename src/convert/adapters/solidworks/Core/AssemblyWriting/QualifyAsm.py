from dataclasses import replace as ReplaceValue

from convert.adapters.base.WriteResult import WriteResult


# the normal boundary reports the measured owned planar bundle without changing any independently generated constructor bytes
def QualifyAsm(ResultValue: WriteResult) -> WriteResult:
    return ReplaceValue(
        ResultValue,
        application_usable=True,
        vendor_loadable=True,
        metadata={
            **ResultValue.metadata,
            "native_qualification": "2026_ordinary_owned_planar_assembly",
            "output_scope": "one_assembly_and_one_owned_part",
            "overwrite_supported": False,
        },
    )
