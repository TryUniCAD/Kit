import json as JsonTools
from pathlib import Path

from ObjectMap import ObjectMap


# authorized mentions need an acknowledgement before source collection or model setup can fail
def ReactionContext(StateName: str) -> dict[str, object]:
    ContextPath = Path("ReviewInput/Context.json")
    if ContextPath.exists():
        return ObjectMap(JsonTools.loads(ContextPath.read_text()))
    if StateName != "started":
        raise ValueError("Completion requires the selected revision context")
    EventData = ObjectMap(JsonTools.loads(Path("ReviewRequest/Event.json").read_text()))
    return {"mention_comment": ObjectMap(EventData["comment"])["id"]}
