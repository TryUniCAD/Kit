# authored style text must remain explicit and cannot borrow localized strings from a saved document or installed resource
def ReadStyleText(ValueInput: object, NameValue: str) -> str:
    if not isinstance(ValueInput, str) or "\x00" in ValueInput:
        raise ValueError(f"{NameValue} must be authored text without nul characters")
    return ValueInput
