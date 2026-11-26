from dataclasses import replace as ReplaceData

from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.MaterialCodec.Package.Model.PackageFolder import (
    PackageFolder,
)
from tests.Convert.Api.Fusion.SavedCuboid.CheckCustody import CheckCustody
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# the material fixture keeps the real saved cuboid relationships and gives its package explicit new resources
def ResourceDoc(Folder: PackageFolder) -> DocumentModel:
    CaseValue = KSavedCases[0]
    Source = SavedSource(CaseValue)
    Payload = Source.read_bytes()
    CheckCustody(Source, CaseValue, Payload)
    Model = ReadDocument(Payload)
    (Material,) = Model.Materials
    Updated = ReplaceData(
        Material, Package=ReplaceData(Material.Package, Resources=Folder)
    )
    return ReplaceData(Model, Materials=(Updated,))
