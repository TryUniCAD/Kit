from dataclasses import replace as ReplaceData
from pathlib import PurePosixPath as AssetPath

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField


# a coherent shared identity isolates the scoped collision guard from missing part checks
def AliasConfigPart(Payload: bytes) -> bytes:
    Model = ReadDocument(Payload)
    Table, Rules = Model.Configurations
    assert Table.KindValue == "table" and Rules.KindValue == "rule"
    Identity = Table.Name.rsplit(".", 2)[-2]
    Alias = f"DesignConfigurationTable.BlobParts/DesignConfigurationRule.{Identity}.dsgcfgrule"
    RootNode = BuildGraph(Model).OneClass("DesignConfigurationRuleSerializerTrigger")
    Edited = ChangeField(Model, RootNode.ObjectId, "partName", AssetPath(Alias).name)
    return EmitParsed(
        ReplaceData(Edited, Configurations=(Table, ReplaceData(Rules, Name=Alias)))
    )
