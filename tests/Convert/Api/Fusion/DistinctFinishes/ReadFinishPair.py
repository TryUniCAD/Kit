from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields, TextValue
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.Formats.Fusion.DocumentCodec.Materials.ProjectMaterial import (
    ProjectMaterial,
)
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.Reading.Materials.BindMaterials import (
    BindMaterials,
)
from convert.Formats.Fusion.DocumentCodec.Reading.Materials.ResolveMatAsset import (
    ResolveMatAsset,
)
from convert.Formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset


# independently resolve both finish owners so different appearance data cannot hide a shared reference
def ReadFinishPair(Payload: bytes) -> tuple[MaterialSpec, MaterialAsset]:
    Model = ReadDocument(Payload)
    Graph = BuildGraph(Model)
    Context = SelectExtrusion(Graph)
    Physical = ObjectFields(Context.BodyNode.Fields["physicalMaterial"])
    Visual = ObjectFields(Context.BodyNode.Fields["visualMaterial"])
    Manager = Graph.Resolve(Physical["ProteinAssetManager"])
    assert Graph.Resolve(Visual["ProteinAssetManager"]) == Manager
    Package = BindMaterials(Model)[Manager.ObjectId]
    Identity = TextValue(Physical["assetReference"])
    BodyAsset = ResolveMatAsset(Package, Identity)
    Appearance = ResolveMatAsset(Package, TextValue(Visual["assetReference"]))
    assert BodyAsset is not None and Appearance is not None
    Links = next(
        Entry.Connections
        for Entry in BodyAsset.Properties
        if Entry.FieldName == "physmat_aspects"
    )
    assert (
        Links is not None
        and Links.Enabled
        and Appearance.InstanceId not in Links.Targets
    )
    assert Appearance.AssetRole == "materialappearance"
    return ProjectMaterial(Package, Identity), Appearance
