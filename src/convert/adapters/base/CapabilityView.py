from __future__ import annotations

from typing import Mapping as TypeMap
from typing import cast as CastValue

from interchange import Capability

from convert.adapters.base.SourceEvidenceKey import KSourceEvidence
from convert.adapters.base.TransferContract import CapTransfer
from convert.adapters.base.TransferContract import CarrierReason
from convert.adapters.base.TransferContract import TransferMode
from convert.adapters.base.WriteValidate import GetCarrierCaps
from convert.adapters.base.WriteValidate import GetNativeCaps
from convert.adapters.base.WriteValidate import IsObjectMap


# preservation evidence and verdicts stay readable through one typed capability view
class CapabilityView:
    __slots__ = ()

    # callers need one complete preservation view independent from representation mode
    @property
    def TransferCaps(self) -> frozenset[Capability]:
        Transfers = CastValue(tuple[CapTransfer, ...], getattr(self, "transfers"))
        return frozenset(TransferData.capability for TransferData in Transfers)

    # canonical native capability access supports both modern and historical result consumers
    @property
    def NativeCaps(self) -> frozenset[Capability]:
        Transfers = CastValue(tuple[CapTransfer, ...], getattr(self, "transfers"))
        return GetNativeCaps(Transfers)

    # canonical carrier capability access keeps reversible preservation evidence directly typed
    @property
    def CarrierCaps(self) -> frozenset[Capability]:
        Transfers = CastValue(tuple[CapTransfer, ...], getattr(self, "transfers"))
        return GetCarrierCaps(Transfers)

    # whole source roundtrip safety includes byte replay for retained source archives
    @property
    def IsRoundtripSafe(self) -> bool:
        Metadata = CastValue(TypeMap[str, object], getattr(self, "metadata"))
        Evidence = Metadata.get(KSourceEvidence)
        return not getattr(self, "dropped") and (
            not IsObjectMap(Evidence)
            or Evidence.get("source_native_byte_replay") is not False
        )

    # near losslessness requires usable output and only intrinsic target format limitations
    @property
    def IsNearLossless(self) -> bool:
        ApplicationUsable = CastValue(bool, getattr(self, "application_usable"))
        VendorLoadable = CastValue(bool, getattr(self, "vendor_loadable"))
        Requirements = CastValue(tuple[str, ...], getattr(self, "requirements"))
        Dropped = CastValue(frozenset[Capability], getattr(self, "dropped"))
        Transfers = CastValue(tuple[CapTransfer, ...], getattr(self, "transfers"))
        return (
            ApplicationUsable
            and VendorLoadable
            and not Requirements
            and not Dropped
            and all(
                TransferData.carrier_reason is CarrierReason.KTargetGap
                for TransferData in Transfers
                if TransferData.mode in {TransferMode.KCarrier, TransferMode.KMixed}
            )
        )
