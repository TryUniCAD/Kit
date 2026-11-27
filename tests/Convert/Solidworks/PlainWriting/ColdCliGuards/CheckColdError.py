# complete process diagnostics must identify the actual source defense rather than an unrelated preflight rejection
def CheckColdError(ErrorValue: dict[str, object], ModeName: str) -> None:
    Message = ErrorValue["message"]
    assert isinstance(Message, str)
    if ModeName in ("binding", "feature", "metadata"):
        assert ErrorValue["error"] == "ValueError"
        assert "cold readback differs from its regenerated part" in Message
    elif ModeName == "fake":
        assert ErrorValue["error"] == "ValueError"
        assert "unqualified SOLIDWORKS sketch support references" in Message
    else:
        assert ErrorValue["error"] == "AdapterNotFoundError"
        assert "does not support the destination" in Message
