# equivalent source boolean words must be retained when their normalized value agrees
def NormalizeFlag(Value: object) -> int:
    return int(Value != 0)
