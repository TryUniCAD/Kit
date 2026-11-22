from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Archive.Construction.Part.Imports.ImportCandidate import ImportCandidate
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from convert.adapters.solidworks.Core.Writing.Measured.MatchPartMeas import (
    MatchPartMeas,
)
from convert.adapters.solidworks.Core.Writing.Measured.PublishMeasMut import (
    PublishMeasMut,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import ReadPartMeas
from convert.adapters.solidworks.Core.Preparation.Chamfers.IsDistChmf import IsDistChmf
from convert.adapters.solidworks.Core.Preparation.Ellipse.IsEllipsePart import (
    IsEllipsePart,
)
from convert.adapters.solidworks.Core.Preparation.Sweeps.IsSweepPart import IsSweepPart
from convert.adapters.solidworks.Core.Writing.Chamfers.EmitPairMut import EmitPairMut
from convert.adapters.solidworks.Core.Writing.Ellipse.EmitEllipMut import EmitEllipMut
from convert.adapters.solidworks.Core.Writing.Sweeps.EmitSweepMut import EmitSweepMut
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Capability

# a bare import transfers the closed boundary and active configuration as native objects
KImportTransfers = (
    CapTransfer(Capability.KBrep, TransferMode.KNative),
    CapTransfer(Capability.KConfigurations, TransferMode.KNative),
)


# publication verifies the complete regenerated archive before touching either kind of output target
def EmitNativeMut(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult:
    ReadbackValue = IsColdRead(DocumentValue)
    if not ReadbackValue:
        if IsSweepPart(DocumentValue):
            return EmitSweepMut(DocumentValue, TargetValue, OptionsValue)
        if IsDistChmf(DocumentValue):
            return EmitPairMut(DocumentValue, TargetValue, OptionsValue)
        if IsEllipsePart(DocumentValue):
            return EmitEllipMut(DocumentValue, TargetValue, OptionsValue)
    SettingsValue = CheckPartOpts(OptionsValue)
    WrittenAt, Receipt = ReadPartMeas(SettingsValue)
    OutputPath = (
        FilePath(TargetValue).expanduser().resolve()
        if isinstance(TargetValue, (str, FilePath))
        else None
    )
    Candidate = PrepareNative(
        DocumentValue, OutputPath or TargetValue, WrittenAt, SettingsValue
    )
    Payload = Candidate.BytesValue
    Evidence = MatchPartMeas(Receipt, Payload)
    Transfers: tuple[CapTransfer, ...] = (
        KImportTransfers if isinstance(Candidate, ImportCandidate) else ()
    )
    if ReadbackValue:
        Transfers = tuple(
            CapTransfer(CapabilityValue, TransferMode.KNative)
            for CapabilityValue in sorted(DocumentValue.capabilities)
        )
    return PublishMeasMut(
        TargetValue, OutputPath, SettingsValue, Payload, Evidence, Transfers
    )
