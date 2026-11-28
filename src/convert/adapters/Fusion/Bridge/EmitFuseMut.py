from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.base.UsabilityError import UsabilityError
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.Fusion.Bridge.EncodeDocument import EncodeDocument
from convert.adapters.Fusion.Measurement.FusionMeasOpt import KFusionMeasOpt
from convert.adapters.Fusion.Measurement.MatchFuseMeas import MatchFuseMeas
from convert.adapters.Fusion.Bridge.WritePayloadMut import WritePayloadMut
from convert.adapters.Fusion.Bridge.WriterInfo import KWriterInfo
from convert.adapters.registry.EquationWrite import CheckEquations
from convert.adapters.registry.InchWrite import CheckInchWrite
from convert.adapters.registry.ResearchWrite import CheckResearch
from convert.adapters.registry.SupportWrite import CheckSupports
from convert.adapters.registry.NativeWrite import CheckNative
from interchange.document.Models.DocumentCaps import InferCaps
from interchange.document.Models.DocumentModel import CadDocument


# measured native publication validates all evidence before the destination is opened
def EmitFuseMut(
    Document: CadDocument,
    Target: KTargetType,
    Options: WriteOptions | None,
) -> WriteResult:
    CheckResearch(Document)
    CheckInchWrite(Document)
    CheckEquations(Document)
    CheckSupports(Document)
    CheckNative(Document)
    Settings = Options if Options is not None else WriteOptions()
    if (
        Settings.configuration is not None
        or Settings.destination_format not in (None, "fusion.f3d", "f3d")
        or set(Settings.values)
        - {
            "final_destination",
            "final_overwrite",
            "allow_carrier",
            "require_self_contained",
            "require_native_transfers",
            "allow_non_native",
            "portable",
            KFusionMeasOpt,
        }
    ):
        raise ValueError("Unsupported Fusion write options")
    Payload = EncodeDocument(Document)
    CapsValue = InferCaps(Document) | Document.capabilities
    if CapsValue - KWriterInfo.capabilities:
        raise ValueError("Unsupported Fusion document capabilities")

    # ordering by value value must stay deterministic so native adapter translation resolves equivalent inputs consistently
    Transfers = tuple(
        CapTransfer(Value, TransferMode.KNative)
        for Value in sorted(CapsValue, key=lambda Value: Value.value)
    )
    Evidence = (
        MatchFuseMeas(Settings.values[KFusionMeasOpt], Payload)
        if KFusionMeasOpt in Settings.values
        else {}
    )
    IsMeasured = bool(Evidence)
    if not IsMeasured and Settings.values.get("allow_carrier") is False:
        raise UsabilityError(
            KWriterInfo.format_id,
            WriteResult(
                None,
                KWriterInfo.format_id,
                0,
                transfers=Transfers,
                requirements=(KFusionMeasOpt,),
            ),
        )
    PathValue = WritePayloadMut(Target, Payload, Settings)
    return WriteResult(
        PathValue,
        KWriterInfo.format_id,
        len(Payload),
        metadata=Evidence,
        transfers=Transfers,
        application_usable=IsMeasured,
        vendor_loadable=IsMeasured,
    )
