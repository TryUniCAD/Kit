from dataclasses import dataclass as MakeDataClass
from re import fullmatch as MatchText

from convert.Formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks

# the family discriminator identifies face appearance tags in reads and writes
KMaterialFamily = "NEUTRON_Material_attrib_def"


# the native tag spelling must survive exact journal emission
@MakeDataClass(frozen=True, slots=True)
class MaterialAttrib:
    Links: AttribLinks
    Tag: str

    # the journal tag must name a uuid before it can bind a design face appearance
    def __post_init__(self) -> None:
        if (
            MatchText(r"[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}", self.Tag)
            is None
        ):
            raise ValueError("Invalid Fusion journal face material tag")
