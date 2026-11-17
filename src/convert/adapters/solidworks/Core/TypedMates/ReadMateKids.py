from pathlib import PureWindowsPath

from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarChild
from convert.adapters.solidworks.Core.TypedMates.PublicMateEnv import PublicMateEnv
from convert.adapters.solidworks.Core.TypedMates.ReadMateChild import ReadMateChild


# basename lookup needs an exact unique child identity before the existing planar projection can use it
def ReadMateKids(EnvValue: PublicMateEnv) -> dict[tuple[str, int], PlanarChild]:
    Result: dict[tuple[str, int], PlanarChild] = {}
    Owners: dict[tuple[str, int], tuple[str, str]] = {}
    for Definition in EnvValue.NativeValue.definitions:
        if Definition.object_id == EnvValue.NativeValue.root_definition_id:
            continue
        Document = EnvValue.DocumentsValue[Definition.object_id]
        SourcePath = EnvValue.PathsValue[Definition.object_id]
        KeyValue = (
            PureWindowsPath(Definition.source_path).name.casefold(),
            Definition.configuration_id,
        )
        Identity = (str(SourcePath.resolve()), Document.source.sha256)
        if KeyValue in Owners and Owners[KeyValue] != Identity:
            raise ValueError(
                "typed mate children have ambiguous basenames and configurations"
            )
        if KeyValue not in Result:
            Result[KeyValue] = ReadMateChild(SourcePath, Document.source.sha256)
            Owners[KeyValue] = Identity
    return Result
