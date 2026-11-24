from pathlib import Path as FilePath


# saved paths must use consistent home expansion instead of platform dependent guesses for other accounts
def PresetPath(Value: object) -> str:
    if not isinstance(Value, str):
        raise ValueError("Run defaults paths must be absolute")
    Parsed = FilePath(Value)
    if (
        not Parsed.anchor
        and Parsed.parts
        and Parsed.parts[0].startswith("~")
        and Parsed.parts[0] != "~"
    ):
        raise ValueError("Run defaults only expand the current user home")
    Expanded = Parsed.expanduser()
    if not Expanded.is_absolute():
        raise ValueError("Run defaults paths must be absolute")
    return str(Expanded)
