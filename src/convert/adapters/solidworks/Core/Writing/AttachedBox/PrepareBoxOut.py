from hashlib import sha256 as CalcSha

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PrepareBoxAxes import (
    PrepareBoxAxes,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.ProjectBoxAxes import (
    ProjectBoxAxes,
)
from convert.adapters.base.SourceEvidenceKey import KSourceEvidence
from convert.adapters.solidworks.Core.Writing.AttachedBox.CheckBoxTarget import (
    CheckBoxTarget,
)
from convert.adapters.solidworks.Core.Writing.AttachedBox.BoxProof import BoxProof
from convert.adapters.solidworks.Core.Writing.AttachedBox.BoxOutputPlan import (
    BoxOutputPlan,
)
from convert.adapters.solidworks.Core.Writing.AttachedBox.ReadBoxMeasure import (
    ReadBoxMeasure,
)
from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from interchange.Core.Common import FreezeMapping


# only the exactly measured native output becomes publishable after complete source verification
def PrepareBoxOut(
    ProofValue: BoxProof, TargetValue: KTargetType, OptionsValue: WriteOptions | None
) -> BoxOutputPlan:
    PlanValue = ProofValue.PlanValue
    SourceValue = PlanValue.PartSource
    Settings = CheckPartOpts(OptionsValue)
    if Settings.configuration not in (
        None,
        SourceValue.ModelValue.configurations[0].name,
    ):
        raise ValueError(
            "attached box publication requires its actual active configuration"
        )
    Measured = ReadBoxMeasure(Settings, PlanValue)
    OutputPath = CheckBoxTarget(TargetValue, Measured)
    Candidate = PrepareBoxAxes(
        SourceValue.ModelValue,
        Measured.NativePath,
        SourceValue.CreationEpoch,
        SourceValue.PropertiesValue,
        ProjectBoxAxes(PlanValue.OriginAxes),
    )
    Payload = Candidate.BytesValue
    if (
        len(Payload) != Measured.ByteCount
        or CalcSha(Payload).hexdigest() != Measured.OutputDigest
    ):
        raise ValueError(
            "regenerated attached box differs from the measured whole archive"
        )
    Evidence = FreezeMapping(
        {
            KSourceEvidence: ProofValue.EvidenceValue,
            KPartMeasureOpt: FreezeMapping(
                {
                    "generated_sha256": Measured.OutputDigest,
                    "oracle_build": KOraclePart["build"],
                    "native_result_sha256": Measured.TerminalDigest,
                }
            ),
        }
    )
    Transfers = tuple(
        CapTransfer(Value, TransferMode.KNative)
        for Value in sorted(ProofValue.NativeCaps)
    )
    return BoxOutputPlan(
        OutputPath, Measured.SettingsValue, Payload, Evidence, Transfers
    )
