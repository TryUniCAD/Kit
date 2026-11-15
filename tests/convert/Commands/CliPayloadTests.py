from pathlib import Path as FilePath

from pytest import mark as TestMark

from interchange.payloads.PayloadRoles import PayloadRole
from tests.convert.Commands.BuildPayload import BuildPayload
from tests.convert.Commands.CheckJsonBlock import CheckJsonBlock
from tests.convert.Commands.WrapDocument import WrapDocument


@TestMark.parametrize("RoleValue", tuple(PayloadRole))
@TestMark.parametrize("HasData", (False, True))
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckPayload(
    RoleValue: PayloadRole,
    HasData: bool,
    IsNested: bool,
    HasOutput: bool,
    TmpPath: FilePath,
) -> None:
    Document = BuildPayload(RoleValue, HasData)
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "RetainedPayload", HasOutput, TmpPath)
