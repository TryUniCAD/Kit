from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.Circle.IsCircRead import IsCircRead
from convert.adapters.solidworks.Core.Preparation.Ellipse.IsEllipRead import IsEllipRead
from convert.adapters.solidworks.Core.Preparation.Equations.HasEqIntent import (
    HasEqIntent,
)
from convert.adapters.solidworks.Core.Preparation.Imports.HasBareBrep import HasBareBrep
from convert.adapters.solidworks.Core.Preparation.Imports.IsImportRead import (
    IsImportRead,
)
from convert.adapters.solidworks.Core.Preparation.IsStockChain import IsStockChain
from convert.adapters.solidworks.Core.Preparation.Materials.PlanMatPart import (
    IsPhysicalMat,
)
from convert.adapters.solidworks.Core.Preparation.OffsetPlane.IsOffRead import IsOffRead
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from convert.adapters.solidworks.Core.Preparation.Revolve.Readback.IsRevRead import (
    IsRevRead,
)
from convert.adapters.solidworks.Core.Writing.Imports.EmitImportMut import EmitImportMut
from convert.adapters.solidworks.Core.Writing.Materials.EmitMatPartMut import (
    EmitMatPartMut,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.PlanThinPart import (
    HasThinWrite,
)
from convert.adapters.solidworks.Core.Writing.Measured.EmitEqMut import EmitEqMut
from convert.adapters.solidworks.Core.Writing.Measured.MatchPartMeas import (
    MatchPartMeas,
)
from convert.adapters.solidworks.Core.Writing.Measured.PublishMeasMut import (
    PublishMeasMut,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import ReadPartMeas
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.EmitPrincMut import (
    EmitPrincMut,
)
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.HasPrincRev import (
    HasPrincRev,
)
from convert.adapters.solidworks.Core.Preparation.Chamfers.IsChmfPart import IsChmfPart
from convert.adapters.solidworks.Core.Preparation.Ellipse.IsEllipsePart import (
    IsEllipsePart,
)
from convert.adapters.solidworks.Core.Preparation.Sweeps.IsSweepPart import IsSweepPart
from convert.adapters.solidworks.Core.Writing.Chamfers.EmitChmfMut import EmitChmfMut
from convert.adapters.solidworks.Core.Writing.Circle.CanWriteCircle import HasCircWrite
from convert.adapters.solidworks.Core.Writing.Circle.EmitCircMut import EmitCircMut
from convert.adapters.solidworks.Core.Writing.OffsetPlanes.CanWriteOffset import (
    HasOffsetWrite,
)
from convert.adapters.solidworks.Core.Writing.OffsetPlanes.EmitOffsetMut import (
    EmitOffsetMut,
)
from convert.adapters.solidworks.Core.Writing.Ellipse.EmitEllipMut import EmitEllipMut
from convert.adapters.solidworks.Core.Writing.Stocks.WriteStocksMut import (
    WriteStocksMut,
)
from convert.adapters.solidworks.Core.Writing.Sweeps.EmitSweepMut import EmitSweepMut
from convert.adapters.solidworks.Core.Preparation.Patterns.IsPatPart import IsPatPart
from convert.adapters.solidworks.Core.Preparation.Patterns.Readback.IsPatRead import (
    IsPatRead,
)
from convert.adapters.solidworks.Core.Writing.Patterns.EmitPatMut import EmitPatMut
from convert.adapters.solidworks.Core.Writing.Measured.Thin.EmitThinMut import (
    EmitThinMut,
)
from convert.adapters.solidworks.Core.Writing.RevolveEnds.EmitRevEndMut import (
    EmitRevEndMut,
)
from convert.adapters.solidworks.Core.Writing.RevolveEnds.HasOrdRevEnd import (
    HasOrdRevEnd,
)
from convert.adapters.solidworks.Core.Writing.RevolveEnds.HasRevEndMeas import (
    HasRevEndMeas,
)
from interchange.document.Models.DocumentModel import CadDocument


# a fresh feature intent selects its measurement before the generic archive fallback
def EmitFreshMut(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult | None:
    if IsImportRead(DocumentValue):
        return EmitImportMut(DocumentValue, TargetValue, OptionsValue)
    if IsPatPart(DocumentValue) or IsPatRead(DocumentValue):
        return EmitPatMut(DocumentValue, TargetValue, OptionsValue)
    if HasThinWrite(DocumentValue):
        return EmitThinMut(DocumentValue, TargetValue, OptionsValue)
    if HasOrdRevEnd(DocumentValue) and HasRevEndMeas(OptionsValue):
        return EmitRevEndMut(DocumentValue, TargetValue, OptionsValue)
    if HasPrincRev(DocumentValue):
        return EmitPrincMut(DocumentValue, TargetValue, OptionsValue)
    if IsStockChain(DocumentValue):
        return WriteStocksMut(DocumentValue, TargetValue, OptionsValue)
    if IsSweepPart(DocumentValue):
        return EmitSweepMut(DocumentValue, TargetValue, OptionsValue)
    if IsChmfPart(DocumentValue):
        return EmitChmfMut(DocumentValue, TargetValue, OptionsValue)
    if IsEllipsePart(DocumentValue):
        return EmitEllipMut(DocumentValue, TargetValue, OptionsValue)
    if HasOffsetWrite(DocumentValue):
        return EmitOffsetMut(DocumentValue, TargetValue, OptionsValue)
    if HasCircWrite(DocumentValue):
        return EmitCircMut(DocumentValue, TargetValue, OptionsValue)
    return None


# publication verifies the complete regenerated archive before touching either kind of output target
def EmitNativeMut(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult:
    if IsPhysicalMat(DocumentValue):
        return EmitMatPartMut(DocumentValue, TargetValue, OptionsValue)
    if IsRevRead(DocumentValue):
        return EmitPrincMut(DocumentValue, TargetValue, OptionsValue)
    if IsOffRead(DocumentValue):
        return EmitOffsetMut(DocumentValue, TargetValue, OptionsValue)
    if IsCircRead(DocumentValue):
        return EmitCircMut(DocumentValue, TargetValue, OptionsValue)
    if IsEllipRead(DocumentValue):
        return EmitEllipMut(DocumentValue, TargetValue, OptionsValue)
    ReadbackValue = IsColdRead(DocumentValue)
    if not ReadbackValue or IsImportRead(DocumentValue) or IsPatRead(DocumentValue):
        FreshValue = EmitFreshMut(DocumentValue, TargetValue, OptionsValue)
        if FreshValue is not None:
            return FreshValue
    if HasEqIntent(DocumentValue):
        return EmitEqMut(DocumentValue, TargetValue, OptionsValue)
    if not ReadbackValue and HasBareBrep(DocumentValue):
        return EmitImportMut(DocumentValue, TargetValue, OptionsValue)
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
    Transfers: tuple[CapTransfer, ...] = ()
    if ReadbackValue:
        Transfers = tuple(
            CapTransfer(CapabilityValue, TransferMode.KNative)
            for CapabilityValue in sorted(DocumentValue.capabilities)
        )
    return PublishMeasMut(
        TargetValue, OutputPath, SettingsValue, Payload, Evidence, Transfers
    )
