from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import (
    IsLineState,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord


# dormant original dimension slots can carry unknown authored variants independently of the active drivers
def CheckPatOrig(RecordValue: object) -> None:
    Fields = NativeRecord(RecordValue)
    if (
        Fields.get("f00") != 1
        or Fields.get("f08") is not None
        or any(Fields.get(NameValue) != -1 for NameValue in ("fc8", "fcc", "f218"))
        or any(
            Fields.get(NameValue) != 0
            for NameValue in (
                "has_f10",
                "f18",
                "f20",
                "fb4",
                "fb8",
                "fc0",
                "f260",
                "fd0",
                "fd4",
                "f1d8",
                "f1d0",
                "f1d4",
                "has_f228",
                "n1e0",
                "f1c0",
                "f25c",
            )
        )
        or not IsLineState(Fields.get("f1e0"))
        or not IsLineState(Fields.get("f1b0"))
    ):
        raise ValueError("pattern carries an alternate original dimension record")
