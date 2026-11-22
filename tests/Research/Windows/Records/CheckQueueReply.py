from json import loads as DecodeJson


# response assertions keep publication orchestration separate from expected queue custody outcomes
def CheckQueueReply(
    ResponseText: str, HostIdentity: dict[str, object], ReleaseHandle: bool
) -> None:
    Response = DecodeJson(ResponseText)
    if ReleaseHandle:
        assert Response["status"] == "completed"
        assert Response["host"] == HostIdentity
        assert Response["provider"] == "fixture.transport"
        assert Response["proof"]["native_qualified"] is False
        return
    assert Response["outcome"] == "waiting_application"
    assert "bounded deadline" in Response["reason"]
    assert Response["native_qualified"] is False
