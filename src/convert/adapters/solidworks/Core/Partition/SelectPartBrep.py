from convert.adapters.base import ReadOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KLocalBodyStream
from convert.adapters.solidworks.Core.Native import NativeFeature
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.Partition.ActivePartition import ActivePartition
from convert.adapters.solidworks.Core.Partition.ActivePartition import ReadActivePart
from convert.adapters.solidworks.Core.Partition.TypedBodyId import TypedBodyId
from convert.adapters.solidworks.Core.Partition.TypedBrep import TypedBrep
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.FindLocalOwner import (
    FindLocalOwner,
)
from interchange import BrepModel
from interchange import BrepPayload
from interchange import Diagnostic as DiagValue


# active partition ownership takes precedence over inferred local geometry
def SelectPartBrep(
    Archive: SldprtArchive,
    Model: NativeModel,
    Settings: ReadOptions,
    Payloads: tuple[BrepPayload, ...],
    HasPayloadDiags: bool,
    ColdBrep: BrepModel | None,
    ConfigurationCount: int,
) -> tuple[
    BrepModel | None, NativeFeature | None, DiagValue | None, ActivePartition | None
]:
    Candidate = (
        FindLocalOwner(Model)
        if Settings.include_brep
        and not Settings.extract_raw_brep
        and Model.active_configuration_id == 0
        and ConfigurationCount == 1
        and not HasPayloadDiags
        else None
    )
    ActivePart = (
        ReadActivePart(
            Payloads,
            Model.active_configuration_id,
            TypedBodyId(Model),
            (Record.name for Record in Archive.records),
        )
        if Candidate is None
        else None
    )
    if ActivePart is not None or ColdBrep is not None:
        BrepValue, LocalOwner, LocalDiag = (
            ActivePart.ModelValue if ActivePart is not None else ColdBrep,
            None,
            None,
        )
    else:
        BrepValue, LocalOwner, LocalDiag = TypedBrep(
            Payloads,
            LocalOwner=Candidate,
            GroupData=Archive.get(KLocalBodyStream) if Candidate is not None else None,
            Strict=Settings.strict,
        )
    return BrepValue, LocalOwner, LocalDiag, ActivePart
