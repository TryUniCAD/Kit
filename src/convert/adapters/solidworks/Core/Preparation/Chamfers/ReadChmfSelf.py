from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.RequirePartPath import RequirePartPath
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the snapshot construction event must agree across the typed self records and both headers
def ReadChmfSelf(Payload: bytes) -> SelfFileInput:
    Archive = SldprtArchive.from_bytes(Payload)
    if Archive.format_version != 4 or ContainerMo(Archive.streams) != 19000:
        raise ValueError("cold chamfer JSON requires a version 19000 part")
    Recipes: list[SelfFileInput] = []
    for NameValue in ("Header2", "Contents/Config-0-ModelHeader"):
        Header = ReadHeaderGraph(Archive.require(NameValue), 19000).FieldsValue
        SelfNode = RequireNative(Header.get("f38"), "moExtObject_c")
        SelfFile = GetFileRef(SelfNode)
        Epoch = SelfNode.FieldsValue.get("f60")
        Shared = NativeRecord(SelfNode.FieldsValue.get("shared"))
        if (
            type(Epoch) is not int
            or (Header.get("f50"), Header.get("f70"), Shared.get("f28"))
            != (Epoch, Epoch, Epoch)
            or SelfFile.KindValue != 2
            or SelfFile.ConfigValue != "Default"
        ):
            raise ValueError("cold chamfer JSON requires one actual self save event")
        Recipes.append(RequirePartPath(SelfFile.PathValue, Epoch))
    TopRecipe, ConfigRecipe = Recipes
    if TopRecipe != ConfigRecipe:
        raise ValueError("cold chamfer JSON self locators disagree")
    return TopRecipe
