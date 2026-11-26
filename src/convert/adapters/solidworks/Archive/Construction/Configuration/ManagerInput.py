from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigSpec import (
    ConfigSpec,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# the manager needs explicit configuration order current selection and its own authored display name without captured defaults
@DataClass(frozen=True, slots=True)
class ManagerInput:
    NameValue: str
    ConfigValues: tuple[ConfigSpec, ...]
    CurrentIndex: int

    # invalid manager inputs must be rejected independently of the global persistent identifier allocation sequence
    def __post_init__(self) -> None:
        if not ReadStyleText(self.NameValue, "configuration manager name"):
            raise ValueError("configuration manager name must not be empty")
        if (
            type(self.ConfigValues) is not tuple
            or not self.ConfigValues
            or any(type(ItemValue) is not ConfigSpec for ItemValue in self.ConfigValues)
        ):
            raise ValueError(
                "configuration manager requires explicit typed configuration inputs"
            )
        if len({ItemValue.NameValue for ItemValue in self.ConfigValues}) != len(
            self.ConfigValues
        ):
            raise ValueError("configuration names must be distinct")
        if type(self.CurrentIndex) is not int or not 0 <= self.CurrentIndex < len(
            self.ConfigValues
        ):
            raise ValueError(
                "current configuration must select an authored configuration"
            )
