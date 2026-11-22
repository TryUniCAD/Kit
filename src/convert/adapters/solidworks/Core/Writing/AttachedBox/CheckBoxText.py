from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import (
    PartTextInput,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap


# authored source properties require real measured literal owners on persisted native states
def CheckBoxText(Observation: dict[str, object], TextValue: PartTextInput) -> None:
    Fields = ReadMeasMap(Observation.get("source_properties"))
    if Observation.get("source_summary") != dict(TextValue.SummaryFields) or set(
        Fields
    ) != set(TextValue.DocumentFields):
        raise ValueError("attached box measurement has different source text owners")
    for NameValue, Expected in TextValue.DocumentFields.items():
        Value = ReadMeasMap(Fields[NameValue])
        if (
            Value.get("type") != 30
            or Value.get("raw") != Expected
            or Value.get("resolved") != Expected
            or Value.get("linked") is not False
        ):
            raise ValueError(
                "attached box measured text differs from the literal source"
            )
