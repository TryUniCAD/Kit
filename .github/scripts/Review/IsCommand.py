from typing import cast


# mention requests must contain only an explicitly configured command rather than arbitrary instructions
def IsCommand(BodyText: object, Settings: dict[str, object]) -> bool:
    return (
        isinstance(BodyText, str)
        and len(BodyText) <= 128
        and BodyText.strip().casefold()
        in {
            Command.casefold()
            for Command in cast(list[str], Settings["MentionCommands"])
        }
    )
