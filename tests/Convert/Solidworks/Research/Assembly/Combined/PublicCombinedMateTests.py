from pathlib import Path as FilePath

from convert import open_document as OpenDocument
from convert.adapters.solidworks.Container.Container import SldprtFormatError
from tests.Convert.Solidworks.Research.Assembly.Combined.AddThirdMate import (
    AddThirdMate,
)
from tests.Convert.Solidworks.Research.Assembly.Combined.CheckCombinedRead import (
    CheckCombinedRead,
)
from tests.Convert.Solidworks.Research.Assembly.Combined.MakeCombinedCase import (
    MakeCombinedCase,
)
from tests.Convert.Solidworks.Research.Assembly.Combined.MakeDuplicateWrapper import (
    MakeDuplicateWrapper,
)
from tests.Convert.Solidworks.Research.Assembly.Combined.WriteCombinedCase import (
    WriteCombinedCase,
)


# normal assembly reads need the complete selected lists and a shared wrapper identity namespace
def TestPublicCombinedMates(TmpPath: FilePath) -> None:
    Pair = WriteCombinedCase(TmpPath / "pair", MakeCombinedCase(False))
    CheckCombinedRead(Pair, 2)
    Request = MakeCombinedCase(True)
    AddThirdMate(Request)
    Triple = WriteCombinedCase(TmpPath / "triple", Request)
    CheckCombinedRead(Triple, 3)
    MakeDuplicateWrapper(Triple, Triple)
    try:
        _ = OpenDocument(Triple, include_brep=False, include_tessellation=False)
    except SldprtFormatError as ErrorInfo:
        assert "wrapper identities collide across mates" in str(ErrorInfo)
    else:
        raise AssertionError("a combined assembly admitted a duplicate wrapper id")
