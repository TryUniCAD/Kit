from dataclasses import replace as ReplaceData

from pytest import raises as RaisesError

from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.MaterialCodec.Package.Model.PackageFolder import (
    PackageFolder,
)
from convert.Formats.Fusion.MaterialCodec.Package.PackageLimits import KMaxFolderDepth
from tests.Convert.Api.Fusion.SavedResources.ResourceDoc import ResourceDoc
from tests.Convert.Api.Fusion.SavedResources.ResTree import MakeResCore, MakeResTree


# native archive validation must still refuse invalid material resource paths and excessive nesting
def TestResBounds() -> None:
    Folder = MakeResTree()
    Branch = Folder.Folders[0]
    BadBranch = ReplaceData(
        Branch, Core=ReplaceData(Branch.Core, NameValue="bad/segment")
    )
    BadPath = ReplaceData(Folder, Folders=(BadBranch,))
    with RaisesError(ValueError, match="Invalid material resource folder name"):
        _ = EmitParsed(ResourceDoc(BadPath))
    DeepValue = Branch.Folders[0]
    for Index in range(KMaxFolderDepth):
        DeepValue = PackageFolder(MakeResCore(100 + Index, "branch"), (DeepValue,))
    DeepFolder = ReplaceData(Folder, Folders=(DeepValue,))
    with RaisesError(ValueError, match="folders exceed the depth limit"):
        _ = EmitParsed(ResourceDoc(DeepFolder))
