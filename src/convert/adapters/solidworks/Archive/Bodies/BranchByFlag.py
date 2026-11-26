from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField


# archive flags select these branches independently of the current record or inline field
def BranchByFlag(FlagsValue: dict[str, int], RuleValue: NativeField) -> bool | None:
    ModeValue = RuleValue.ModeValue
    Conditions = FlagsValue.get("conditions", 0)
    if ModeValue == "Context":
        return bool(FlagsValue.get(RuleValue.NameValue, 0))
    if ModeValue in ("Condition", "NotCondition"):
        IsSet = bool(Conditions & RuleValue.MaskValue)
        return IsSet if ModeValue == "Condition" else not IsSet
    if ModeValue == "NotContext":
        return not FlagsValue.get(RuleValue.NameValue, 0)
    if ModeValue == "ConditionsClear":
        return Conditions == 0
    if ModeValue == "PeNoise":
        return bool(
            (FlagsValue.get("pe_active", 0) and FlagsValue.get("pe_helper", 0))
            or FlagsValue.get("pe_file", 0)
        )
    return None
