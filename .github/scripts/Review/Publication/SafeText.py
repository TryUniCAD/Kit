import re as RegexTools


# review text must not create notifications or executable markdown constructs
def SafeText(Value: object) -> str:
    return RegexTools.sub(r"[<>`\[\]\\]", "", str(Value)).replace("@", "＠")
