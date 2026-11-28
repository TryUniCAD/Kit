from dataclasses import replace as ReplaceValue

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatPresentInput import (
    PatPresentInput,
)

# the pattern presentation option carries only authored values owned by the neutral graph
KPatPresentOpt = "solidworks_pattern_presentation"


# the measurement and generic path options stay independent from typed pattern presentation
def ReadPatOptions(
    OptionsValue: WriteOptions | None,
) -> tuple[WriteOptions | None, PatPresentInput | None]:
    if not isinstance(OptionsValue, WriteOptions):
        return OptionsValue, None
    Values = dict(OptionsValue.values)
    Presentation = Values.pop(KPatPresentOpt, None)
    if Presentation is not None and type(Presentation) is not PatPresentInput:
        raise TypeError("linear pattern requires an explicit typed presentation")
    return ReplaceValue(OptionsValue, values=Values), Presentation
