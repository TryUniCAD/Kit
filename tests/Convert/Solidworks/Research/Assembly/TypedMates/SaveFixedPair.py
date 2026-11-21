from base64 import b64decode as DecodeBase
from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath, PureWindowsPath
from typing import cast as CastValue


# public anchor checks need actual independently generated parent and child files rather than manufactured neutral instance records
def SaveFixedPair(
    Request: dict[str, object], BuiltValue: dict[str, object], TargetRoot: FilePath
) -> FilePath:
    TargetRoot.mkdir(parents=True)
    ParentPath: FilePath | None = None
    for RoleValue in ("assembly", "child"):
        InputValue = CastValue(dict[str, object], Request[RoleValue])
        if RoleValue == "child":
            InputValue = CastValue(dict[str, object], InputValue["settings"])
        OutputValue = CastValue(dict[str, object], InputValue["output"])
        NameValue = PureWindowsPath(CastValue(str, OutputValue["path_name"])).name
        ReportValue = CastValue(dict[str, object], BuiltValue[RoleValue])
        BytesValue = DecodeBase(CastValue(str, ReportValue["blob"]), validate=True)
        assert HashBytes(BytesValue).hexdigest() == ReportValue["sha256"]
        SavedPath = TargetRoot / NameValue
        ByteCount = SavedPath.write_bytes(BytesValue)
        assert ByteCount == len(BytesValue)
        if RoleValue == "assembly":
            ParentPath = SavedPath
    assert ParentPath is not None
    return ParentPath
