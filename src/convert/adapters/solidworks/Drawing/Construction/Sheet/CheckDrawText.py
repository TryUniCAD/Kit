# authored names must survive native strings and drawing index separators without silent replacement
def CheckDrawText(TextValue: object, IsIndex: bool) -> None:
    if not isinstance(TextValue, str) or not TextValue or "\x00" in TextValue:
        raise ValueError("drawing sheet construction requires nonempty native names")
    if IsIndex and (
        "@" in TextValue
        or any(
            not (
                ord(Character) in (9, 10, 13)
                or 32 <= ord(Character) <= 55295
                or 57344 <= ord(Character) <= 65533
                or 65536 <= ord(Character) <= 1114111
            )
            for Character in TextValue
        )
    ):
        raise ValueError("drawing sheet text is outside the xml index domain")
