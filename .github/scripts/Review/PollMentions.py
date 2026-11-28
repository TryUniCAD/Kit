import json as JsonTools
import os as OsTools
from pathlib import Path
from Input.SelectMention import SelectMention
from ObjectMap import ObjectMap


# trusted polling admits mentions without exposing privileged workflows to public comment events
def PollMentions() -> None:
    RepoName = OsTools.environ["GITHUB_REPOSITORY"]
    Config = ObjectMap(
        JsonTools.loads(
            Path(".agents/skills/standard-pr-practice/ReviewBot.json").read_text()
        )
    )
    Settings = ObjectMap(Config["AccountReview"])
    EventData = SelectMention(RepoName, Settings)
    if EventData is not None:
        Path("ReviewRequest").mkdir()
        Path("ReviewRequest/Event.json").write_text(JsonTools.dumps(EventData))
        with Path(OsTools.environ["GITHUB_OUTPUT"]).open("a") as OutputFile:
            OutputFile.write("mention=true\n")
        return
    with Path(OsTools.environ["GITHUB_OUTPUT"]).open("a") as OutputFile:
        OutputFile.write("mention=false\n")


if __name__ == "__main__":
    PollMentions()
