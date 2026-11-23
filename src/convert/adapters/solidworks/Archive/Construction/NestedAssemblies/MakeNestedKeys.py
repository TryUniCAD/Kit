from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.MakeAsmKeyIndex import (
    MakeAsmKeyIndex,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# nested keyword references must derive their native type from each actual target rather than reuse one part label across an assembly closure
def MakeNestedKeys(TargetValue: TargetDocument) -> bytes:
    return MakeAsmKeyIndex(
        TargetValue.RootValue,
        TargetValue.FeatureValues,
        TargetValue.HeaderValue,
        TargetValue.CurrentConfig,
        tuple(
            (
                Reference,
                ArchiveNode.RequireNode(ChildValue.HeaderValue.FieldsValue["f38"]),
            )
            for Reference, ChildValue in zip(
                TargetValue.ReferenceValues, TargetValue.ChildTargets, strict=True
            )
        ),
    )
