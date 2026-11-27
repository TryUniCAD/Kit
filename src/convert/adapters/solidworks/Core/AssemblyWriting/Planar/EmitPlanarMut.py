from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import (
    ReadAsmModel,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.PrepareAssembly import (
    PrepareAssembly,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Readback.IsPlanarRead import (
    IsPlanarRead,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Readback.ReadExactPlace import (
    ReadExactPlace,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Readback.PlanarReadIn import (
    PlanarReadIn,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from convert.adapters.solidworks.Core.AssemblyWriting.CheckAsmOpts import CheckAsmOpts
from convert.adapters.solidworks.Core.AssemblyWriting.CheckFreshFiles import (
    CheckFreshFiles,
)
from convert.adapters.solidworks.Core.AssemblyWriting.FinalAsmPath import FinalAsmPath
from convert.adapters.solidworks.Core.AssemblyWriting.Measured.ReadAsmMeas import (
    ReadAsmMeas,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Planar.MatchPlanarMeas import (
    KPlanarMeasSchema,
    MatchPlanarMeas,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Readback.CheckBundleRead import (
    CheckBundleRead,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Readback.ReadbackTransfers import (
    ReadbackTrans,
)
from convert.adapters.solidworks.Core.AssemblyWriting.WriteAsmFiles import WriteAsmFiles
from interchange.document.Models.DocumentModel import CadDocument


# native measurement must cover every regenerated file before staging output
def EmitPlanarMut(
    Document: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult:
    SettingsValue = CheckAsmOpts(OptionsValue)
    WrittenAt, Receipt = ReadAsmMeas(SettingsValue, SchemaValue=KPlanarMeasSchema)
    if not isinstance(TargetValue, (str, FilePath)):
        raise TypeError(
            "planar assembly output requires a staged filesystem destination"
        )
    OutputPath = FilePath(TargetValue).expanduser().resolve()
    FinalPath, NativePath = FinalAsmPath(OutputPath, SettingsValue)
    RequireAsm(
        "final_destination" in SettingsValue.values
        and OutputPath.parent != FinalPath.parent,
        "planar assembly emission requires registry path staging",
    )
    Reopened = IsPlanarRead(Document)
    InputValue = PlanarReadIn(Document) if Reopened else Document
    ModelValue = ReadAsmModel(InputValue)
    RequireAsm(
        len(ModelValue.Occurrences) == 2,
        "measured planar assembly requires two direct component occurrences",
    )
    RequireAsm(
        SettingsValue.configuration
        in (None, ModelValue.ConfigValue.id, ModelValue.ConfigValue.name),
        "requested assembly configuration is unavailable",
    )
    ChildName = ModelValue.ChildValue.name + ".SLDPRT"
    CheckFreshFiles(FinalPath, (ChildName,))
    GraphValue = Document.assembly
    Placements = (
        {Value.id: ReadExactPlace(Value) for Value in GraphValue.instances}
        if Reopened and GraphValue is not None
        else None
    )
    Candidate = PrepareAssembly(
        InputValue, NativePath, WrittenAt, ExactPlacements=Placements
    )
    Companions = ((ChildName, Candidate.ChildValue.BytesValue),)
    Locator = PureWindowsPath(NativePath)
    Members = (
        (Locator.with_name(ChildName), Candidate.ChildValue.BytesValue),
        (Locator, Candidate.BytesValue),
    )
    Evidence = MatchPlanarMeas(
        Receipt,
        Locator,
        tuple((PathValue.name, Payload) for PathValue, Payload in Members),
    )
    if Reopened:
        CheckBundleRead(Document, Members, ScopeValue="planar")
    ResultValue = WriteAsmFiles(OutputPath, Candidate.BytesValue, Companions)
    return ReplaceValue(
        ResultValue,
        metadata={
            **ResultValue.metadata,
            **Evidence,
            "output_scope": "root_and_owned_planar_child",
        },
        transfers=ReadbackTrans(Document) if Reopened else (),
        application_usable=True,
        vendor_loadable=True,
    )
