from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# each runner phase must attest its owned saved input or its expected bracket control
def CheckPairPhase(
    PhaseValue: dict[str, object],
    NameValue: str,
    CheckCount: int,
    SavedHash: str | None,
) -> str:
    if (
        set(PhaseValue)
        != {
            "phase",
            "passed",
            "record_sha256",
            "native_sha256",
            "first_failure",
            "checks",
        }
        or PhaseValue.get("phase") != NameValue
        or PhaseValue.get("passed") is not True
        or PhaseValue.get("first_failure") is not None
        or type(PhaseValue.get("checks")) is not int
        or PhaseValue.get("checks") != CheckCount
        or PhaseValue.get("native_sha256") != SavedHash
    ):
        raise ValueError("distance chamfer measurement has a failed or unowned phase")
    return ReadMeasSha(PhaseValue.get("record_sha256"))
