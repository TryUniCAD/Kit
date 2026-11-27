import re as Regex

from tests.Research.Calibration.Diagnostics.CalJsonTypes import IsJsonRecord


# the terminal event can explain why the controller stopped before a worker result was accepted
def TerminalEvent(Event: object) -> dict[str, object] | None:
    if not IsJsonRecord(Event) or Event.get("event") not in (
        "finished",
        "setup_failed",
        "renew_error",
        "resource_measurement_error",
        "orphan",
    ):
        return None
    if (
        Event["event"] == "finished"
        and Event.get("outcome") == "completed"
        and Event.get("stale") is False
    ):
        return None
    Detail: dict[str, object] = {
        Field: Event[Field] for Field in ("event", "outcome", "stale") if Field in Event
    }
    Receipt = Event.get("receipt")
    if IsJsonRecord(Receipt):
        Detail.update(
            {
                Field: Receipt[Field]
                for Field in ("exit_status", "signal", "stop_reason")
                if Field in Receipt
            }
        )
    Reason = Event.get("error") or Event.get("reason")
    if isinstance(Reason, str):
        Match = Regex.search(
            r"(?:^|: )([A-Za-z][A-Za-z0-9]*(?:Error|Exception|Expired)):", Reason
        )
        if Match:
            Detail["error_type"] = Match[1]
    return Detail
