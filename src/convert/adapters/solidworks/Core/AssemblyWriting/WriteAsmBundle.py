from pathlib import Path as FilePath

from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Archive.Construction.AssemblySets.OrderedAsm import (
    OrderedAsm,
)
from convert.adapters.solidworks.Container.Format import KAsmFormatId
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm


# a complete candidate must publish its single owned child beside the parent while retaining explicitly unmeasured native acceptance
def WriteAsmBundle(Candidate: OrderedAsm, TargetValue: FilePath) -> WriteResult:
    ChildPath = TargetValue.parent / (
        Candidate.ChildValue.PlanValue.NameValue + ".SLDPRT"
    )
    RequireAsm(
        ChildPath.name.casefold() != TargetValue.name.casefold(),
        "generated assembly output filenames collide",
    )
    for PathValue, BufferValue in (
        (TargetValue, Candidate.BytesValue),
        (ChildPath, Candidate.ChildValue.BytesValue),
    ):
        with PathValue.open("xb") as OutputFile:
            CountValue = OutputFile.write(BufferValue)
        if CountValue != len(BufferValue):
            raise OSError("short generated assembly bundle write")
    return WriteResult(
        TargetValue,
        KAsmFormatId,
        len(Candidate.BytesValue),
        metadata={
            "component_file_count": 1,
            "component_file_names": (ChildPath.name,),
            "component_bytes_written": len(Candidate.ChildValue.BytesValue),
            "bundle_bytes_written": len(Candidate.BytesValue)
            + len(Candidate.ChildValue.BytesValue),
            "native_qualification": "unmeasured_portable_assembly_profile",
        },
        application_usable=False,
        vendor_loadable=False,
    )
