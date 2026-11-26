# reserved section state and lookup ownership must match completely before named values become public metadata
def CheckPropBag(
    ReservedValues: dict[int, tuple[str, str]],
    Dictionary: dict[str, int],
    NamesValue: dict[str, int],
    IsConfig: bool,
    IsUser: bool,
) -> None:
    ExpectedValues = (
        {1: ("i2", "65001")}
        if IsUser
        else ({} if IsConfig else {1: ("i2", "65001"), 22: ("bool", "No")})
    )
    if ReservedValues != ExpectedValues or Dictionary != NamesValue:
        raise ValueError(
            "part property reserved state or name dictionary differs from its values"
        )
