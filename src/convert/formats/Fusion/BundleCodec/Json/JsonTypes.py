from typing import TypeAlias

KJsonValue: TypeAlias = (
    None | bool | int | float | str | list["KJsonValue"] | dict[str, "KJsonValue"]
)
