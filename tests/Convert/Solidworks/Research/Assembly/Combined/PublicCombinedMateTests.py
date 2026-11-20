from pathlib import Path as FilePath

from convert import open_document as OpenDocument
from convert.adapters.solidworks.Container.Container import SldprtFormatError
from tests.Convert.Solidworks.Research.Assembly.Combined.AddThirdMate import (
    AddThirdMate,
)
from tests.Convert.Solidworks.Research.Assembly.Combined.CheckCombinedRead import (
    CheckMateRead,
)
from tests.Convert.Solidworks.Research.Assembly.Combined.MakeCombinedCase import (
    MakeMateCase,
)
from tests.Convert.Solidworks.Research.Assembly.Combined.MakeDuplicateWrapper import (
    DuplicateWrap,
)
from tests.Convert.Solidworks.Research.Assembly.Combined.WriteCombinedCase import (
    WriteMateCase,
)


# normal assembly reads need the complete selected lists and a shared wrapper identity namespace
def TestPublicMates(TmpPath: FilePath) -> None:
    PairPath = WriteMateCase(TmpPath / "pair", MakeMateCase(False))
    CheckMateRead(PairPath, 2)
    Request = MakeMateCase(True)
    AddThirdMate(Request)
    Triple = WriteMateCase(TmpPath / "triple", Request)
    CheckMateRead(Triple, 3)
    DuplicateWrap(Triple, Triple)
    try:
        _ = OpenDocument(Triple, include_brep=False, include_tessellation=False)
    except SldprtFormatError as ErrorInfo:
        assert "wrapper identities collide across mates" in str(ErrorInfo)
    else:
        raise AssertionError("a combined assembly admitted a duplicate wrapper id")
