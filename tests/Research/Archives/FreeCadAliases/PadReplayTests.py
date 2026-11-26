from dataclasses import replace as Replace
from pathlib import Path as FilePath

from convert import convert as Convert
from convert import open_document as OpenDocument
from convert import write_document as WriteDocument
from convert.adapters.freecad.Replay.NativeIdentity import (
    KExplicitSketchProfile,
    KReplaySketchAttr,
)
from convert.adapters.freecad.Replay.PrepareReplay import PrepareReplay
from tests.Research.Archives.FreeCadAliases.MakePadFixture import MakePadFixture
from tests.Research.Archives.FreeCadAliases.PreLinkCarrier import PreLinkCarrier


# old carriers with active hidden sketches still need exact archive restoration
def CheckPadReplay(TmpPath: FilePath) -> None:
    Original = MakePadFixture("native")
    Document = OpenDocument(Original, source_format="freecad.fcstd")
    OldModel = PreLinkCarrier(Document)
    assert OldModel.sketches[0].suppressed is False
    assert any(
        Value.attributes.get(KReplaySketchAttr) == KExplicitSketchProfile
        for Value in OldModel.brep_payloads
    )
    Carrier = TmpPath / "native-pad.json"
    _ = WriteDocument(OldModel, Carrier)
    Restored = TmpPath / "restored.FCStd"
    Result = Convert(Carrier, Restored)
    assert Result.output.metadata["mode"] == "exact_native_roundtrip"
    assert Restored.read_bytes() == Original
    Carried = OpenDocument(Carrier)
    Edited = Replace(Carried, sketches=(Replace(Carried.sketches[0], suppressed=True),))
    assert PrepareReplay(Edited, Migrate=False)[1] is None
