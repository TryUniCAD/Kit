# incomplete neutral assembly intent must fail before any native graph or output destination is created
def RequireAsm(IsValid: bool, MessageValue: str) -> None:
    if not IsValid:
        raise ValueError(MessageValue)
