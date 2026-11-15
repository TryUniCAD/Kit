from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Dwg.EmitDwgFile import EmitDwgFile
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFile import DwgFile


# drawing database needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class DrawingDatabase:
    FileName: str
    Model: DwgFile

    # the database content needs a single derivation so a drawing never carries a second copy of the dwg bytes
    @property
    def Content(self) -> bytes:
        return EmitDwgFile(self.Model)
