from pathlib import Path as FilePath

from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Archive.Construction.AssemblySets.OrderedAsm import (
    OrderedAsm,
)
from convert.adapters.solidworks.Core.AssemblyWriting.WriteAsmFiles import WriteAsmFiles


# a flat candidate supplies its shared child and preserves its existing bundle contract
def WriteAsmBundle(Candidate: OrderedAsm, TargetValue: FilePath) -> WriteResult:
    return WriteAsmFiles(
        TargetValue,
        Candidate.BytesValue,
        (
            (
                Candidate.ChildValue.PlanValue.NameValue + ".SLDPRT",
                Candidate.ChildValue.BytesValue,
            ),
        ),
        "unmeasured_portable_assembly_profile",
    )
