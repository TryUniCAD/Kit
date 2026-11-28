from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Container.Format import KAsmFormatId
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm


# sibling staging records written files while the calling publication gate owns native attestation
def WriteAsmFiles(
    TargetValue: FilePath,
    BufferValue: bytes,
    Companions: tuple[tuple[str, bytes], ...],
) -> WriteResult:
    NamesValue = tuple(NameValue for NameValue, _ in Companions)
    RequireAsm(
        all(
            NameValue not in ("", ".", "..")
            and FilePath(NameValue).name == NameValue
            and PureWindowsPath(NameValue).name == NameValue
            for NameValue in NamesValue
        ),
        "generated assembly output must use sibling filenames",
    )
    FoldedNames = {
        TargetValue.name.casefold(),
        *(NameValue.casefold() for NameValue in NamesValue),
    }
    RequireAsm(
        len(FoldedNames) == len(NamesValue) + 1,
        "generated assembly output filenames collide",
    )
    for NameValue, DataValue in ((TargetValue.name, BufferValue), *Companions):
        with (TargetValue.parent / NameValue).open("xb") as OutputFile:
            CountValue = OutputFile.write(DataValue)
        if CountValue != len(DataValue):
            raise OSError("short generated assembly bundle write")
    ChildBytes = sum(len(DataValue) for _, DataValue in Companions)
    return WriteResult(
        TargetValue,
        KAsmFormatId,
        len(BufferValue),
        metadata={
            "component_file_count": len(Companions),
            "component_file_names": NamesValue,
            "component_bytes_written": ChildBytes,
            "bundle_bytes_written": len(BufferValue) + ChildBytes,
            "output_scope": "root_and_owned_nested_dependencies",
            "overwrite_supported": False,
        },
    )
