from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.solidworks.Core.Preparation.Chamfers.IsChmfPart import IsChmfPart
from convert.adapters.solidworks.Core.Preparation.Chamfers.IsDistChmf import IsDistChmf
from convert.adapters.solidworks.Core.Preparation.Chamfers.PlanChmfPart import (
    PlanChmfPart,
)
from convert.adapters.solidworks.Core.Preparation.Ellipse.IsEllipsePart import (
    IsEllipsePart,
)
from convert.adapters.solidworks.Core.Preparation.Ellipse.PlanEllipse import PlanEllipse
from convert.adapters.solidworks.Core.Preparation.Equations.HasEqIntent import (
    HasEqIntent,
)
from convert.adapters.solidworks.Core.Preparation.Equations.PlanEqPart import PlanEqPart
from convert.adapters.solidworks.Core.Preparation.Patterns.IsPatPart import IsPatPart
from convert.adapters.solidworks.Core.Preparation.PlanNativePart import PlanNativePart
from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
from convert.adapters.solidworks.Core.Preparation.Readback.ColdReadInput import (
    ColdReadInput,
)
from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from convert.adapters.solidworks.Core.Preparation.Revolve.Readback.IsRevRead import IsRevRead
from convert.adapters.solidworks.Core.Preparation.Revolve.PlanThinPart import (
    HasThinWrite,
    PlanThinWrite,
)
from convert.adapters.solidworks.Core.Preparation.Sweeps.IsSweepPart import IsSweepPart
from convert.adapters.solidworks.Core.Writing.CanWritePat import CanWritePat
from convert.adapters.solidworks.Core.Writing.AttachedBox.IsBoxSource import IsBoxSource
from convert.adapters.solidworks.Core.Writing.AttachedBox.ProveBoxSource import (
    ProveBoxSource,
)
from convert.adapters.solidworks.Core.Writing.CanWriteSweep import CanWriteSweep
from convert.adapters.solidworks.Core.Writing.Circle.CanWriteCircle import (
    CanWriteCircle,
    HasCircWrite,
)
from convert.adapters.solidworks.Core.Writing.Imports.CanImportPart import CanImportPart
from convert.adapters.solidworks.Core.Writing.IsPartTarget import IsPartTarget
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.CanWriteRev import CanWriteRev
from convert.adapters.solidworks.Core.Writing.OffsetPlanes.CanWriteOffset import (
    CanWriteOffset,
    HasOffsetWrite,
)
from interchange.document.Models.DocumentModel import CadDocument


# cold eligibility must prove the supported sketch and drivers before output staging
def CanWriteCold(DocumentValue: CadDocument, TargetValue: KTargetType) -> bool:
    PathValue = (
        FilePath(TargetValue) if isinstance(TargetValue, (str, FilePath)) else None
    )
    NameValue = (
        PathValue.stem if PathValue is not None else DocumentValue.sketches[0].name
    )
    InputValue = ColdReadInput(DocumentValue, NameValue)
    PlanValue = (
        PlanEqPart(InputValue)[1]
        if HasEqIntent(InputValue)
        else PlanPartWrite(InputValue)
    )
    return IsPartTarget(PlanValue.NameValue, TargetValue) and (
        PathValue is None or not PathValue.is_dir()
    )


# part selection must validate specific editable histories ahead of generic import and ordinary part routes
def CanWritePart(DocumentValue: CadDocument, TargetValue: KTargetType) -> bool:
    try:
        if IsBoxSource(DocumentValue):
            ProofValue = ProveBoxSource(DocumentValue)
            NameValue = ProofValue.PlanValue.PartSource.ModelValue.metadata.get("name")
            return isinstance(NameValue, str) and IsPartTarget(NameValue, TargetValue)
        if IsRevRead(DocumentValue):
            return CanWriteRev(DocumentValue, TargetValue)
        if IsColdRead(DocumentValue):
            return CanWriteCold(DocumentValue, TargetValue)
        if HasThinWrite(DocumentValue):
            ThinValue = PlanThinWrite(DocumentValue)
            return IsPartTarget(ThinValue.NameValue, TargetValue)
        if IsSweepPart(DocumentValue):
            return CanWriteSweep(DocumentValue, TargetValue)
        if IsChmfPart(DocumentValue):
            PlanChmf = PlanChmfPart(
                DocumentValue, AllowDistancePair=IsDistChmf(DocumentValue)
            )
            return IsPartTarget(PlanChmf.StockValue.NameValue, TargetValue)
        if IsPatPart(DocumentValue):
            return CanWritePat(DocumentValue, TargetValue)
        if IsEllipsePart(DocumentValue):
            EllipseValue = PlanEllipse(DocumentValue)
            return IsPartTarget(EllipseValue.NameValue, TargetValue)
        if HasOffsetWrite(DocumentValue):
            return CanWriteOffset(DocumentValue, TargetValue)
        if HasCircWrite(DocumentValue):
            return CanWriteCircle(DocumentValue, TargetValue)
        if DocumentValue.brep is not None:
            return CanImportPart(DocumentValue, TargetValue)
        PlanValue = PlanNativePart(DocumentValue, AllowMeasuredMid=True)
    except (IndexError, TypeError, ValueError):
        return False
    return IsPartTarget(PlanValue.NameValue, TargetValue)
