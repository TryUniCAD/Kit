from convert.adapters.solidworks.Container.Parasolid import (
    decode_brep_model as DecodeBrepModel,
)
from convert.adapters.solidworks.Core.Native import NativeFeature
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalImport import (
    ReadLocalImport,
)
from interchange import BrepModel
from interchange import BrepPayload
from interchange import Diagnostic as DiagValue
from typing import Sequence


# this definition exists because focused behavior needs one stable owner
def TypedBrep(
    Payloads: Sequence[BrepPayload],
    *,
    Strict: bool,
    LocalOwner: NativeFeature | None = None,
    GroupData: bytes | None = None,
) -> tuple[BrepModel | None, NativeFeature | None, DiagValue | None]:
    Groups: dict[str, list[BrepPayload]] = {}
    for Index, Payload in enumerate(Payloads):
        Groups.setdefault(Payload.source_stream or f"payload:{Index}", []).append(
            Payload
        )
    Models: list[BrepModel] = []
    HasAmbiguous = False
    for Group in Groups.values():
        Decoded = tuple(
            (
                Model
                for Payload in Group
                if Payload.data is not None
                and (Model := DecodeBrepModel(Payload.data)) is not None
            )
        )
        if len(Decoded) == 1:
            Models.append(Decoded[0])
        elif len(Decoded) > 1:
            HasAmbiguous = True
    if Models or HasAmbiguous or LocalOwner is None or GroupData is None:
        return (Models[0] if len(Models) == 1 else None), None, None
    return ReadLocalImport(Payloads, GroupData, LocalOwner, Strict=Strict)
