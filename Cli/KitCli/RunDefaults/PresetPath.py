from pathlib import Path as FilePath


# saved paths must use consistent home expansion instead of platform dependent guesses for other accounts
def PresetPath(Value: object) -> str:
    if not isinstance(Value, str):
        raise ValueError("Run defaults paths must be absolute")
    if Value.startswith("~") and len(Value) > 1 and Value[1] not in "/\\":
        raise ValueError("Run defaults only expand the current user home")
    Expanded = FilePath(Value).expanduser()
    if not Expanded.is_absolute():
        raise ValueError("Run defaults paths must be absolute")
    return str(Expanded)
