from dataclasses import dataclass as DataClass, replace as ReplaceValue

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)

# one scoped option owns the authored presentation independently from the approval record
KOffsetWriteOpt = "solidworks_offset_input"


# explicit authored layout and sketch annotation settings remain outside the native measurement report
@DataClass(frozen=True, slots=True)
class OffsetOptions:
    RecipeValue: PartBuildInput
    RadialTextPoint: tuple[float, float]


# only the scoped offset route accepts these settings while ordinary options retain their current validation
def ReadOffOptions(
    SettingsValue: WriteOptions,
) -> tuple[OffsetOptions, WriteOptions]:
    Values = dict(SettingsValue.values)
    InputValue = Values.pop(KOffsetWriteOpt, None)
    if (
        type(InputValue) is not OffsetOptions
        or type(InputValue.RecipeValue) is not PartBuildInput
    ):
        raise ValueError(
            "offset publication requires its authored part and radial presentation"
        )
    return InputValue, ReplaceValue(SettingsValue, values=Values)
