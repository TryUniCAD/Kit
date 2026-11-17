from ntpath import normcase as NormCase, normpath as NormPath
from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Header.NativeFileRef import NativeFileRef
from convert.adapters.solidworks.Archive.Header.NativeHeader import NativeHeader
from convert.adapters.solidworks.Container.Format import KPartSuffix
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Drawing.Metadata.SavedSheet import SavedSheet


# keyword relations must agree with the actual native header directory entry
def JoinModelRef(
    Header: NativeHeader, Sheet: SavedSheet, ViewList: str
) -> NativeFileRef | None:
    if not Sheet.ViewName:
        if Header.ModelFiles or Header.Bounds is not None or ViewList != "0:":
            raise SldprtFormat("empty drawing has conflicting model references")
        return None
    if len(Header.ModelFiles) != 1 or Header.Bounds is None:
        raise SldprtFormat("drawing view requires a unique header model and bounds")
    Model = Header.ModelFiles[0]
    Fields = ViewList.split("@")
    if (
        len(Fields) != 7
        or Fields[:3] != ["1:", "", Sheet.ConfigName]
        or Fields[5:] != [Sheet.ViewName, Sheet.NameValue]
        or NormCase(NormPath(Fields[4])) != NormCase(NormPath(Model.PathValue))
    ):
        raise SldprtFormat("drawing model and configuration indexes disagree")
    FilePath = PureWindowsPath(Model.PathValue)
    if (
        Model.KindValue != 2
        or Model.ConfigValue
        or FilePath.stem.casefold() != Model.NameValue.casefold()
        or FilePath.name.casefold() != Sheet.ModelName.casefold()
        or FilePath.suffix.casefold() != KPartSuffix
    ):
        raise SldprtFormat("drawing view requires one native external part reference")
    return Model
