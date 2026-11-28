from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# receipt authentication must bound member and locator fields before canonical encoding
def CheckPairRows(Receipt: dict[str, object]) -> None:
    RootValue = Receipt.get("root")
    Namespace = Receipt.get("namespace")
    RequireAsm(
        type(RootValue) is str
        and 0 < len(RootValue) <= 255
        and type(Namespace) is str
        and 0 < len(Namespace) <= 4096,
        "planar evidence requires bounded native locator text",
    )
    MemberRows = ReadMeasRows(Receipt.get("members"), 2)
    RequireAsm(len(MemberRows) == 2, "planar evidence requires both measured members")
    for Entry in MemberRows:
        LabelValue, BytesValue = Entry.get("name"), Entry.get("bytes")
        RequireAsm(
            Entry.keys() == {"name", "bytes", "sha256"}
            and type(LabelValue) is str
            and 0 < len(LabelValue) <= 255
            and type(BytesValue) is int
            and 0 < BytesValue <= 0xFFFFFFFF,
            "planar evidence requires bounded complete member rows",
        )
        _ = ReadMeasSha(Entry.get("sha256"))
