from dataclasses import replace as ReplaceValue

from convert.adapters.base.WriteResult import WriteResult


# only the measured rigid nested profile has native usability for every owned member
def QualifyNested(ResultValue: WriteResult) -> WriteResult:
    return ReplaceValue(
        ResultValue,
        application_usable=True,
        vendor_loadable=True,
        metadata={
            **ResultValue.metadata,
            "native_qualification": "2026_rigid_nested_assembly",
            "output_scope": "root_and_owned_nested_dependencies",
            "overwrite_supported": False,
        },
    )
