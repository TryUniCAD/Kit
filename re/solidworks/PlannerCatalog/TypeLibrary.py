# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from argparse import ArgumentParser
from datetime import date, datetime
from hashlib import sha256
from json import dumps
from math import isfinite
from pathlib import Path

# recorded notices preserve repository ownership in machine readable metadata
KNoticeText = """SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently."""


# inert metadata must never execute vendor code or expose opaque representations
def PlainValue(ValueData):
    if ValueData is None or isinstance(ValueData, (str, int, bool)):
        return ValueData
    if isinstance(ValueData, float):
        return ValueData if isfinite(ValueData) else {"unrepresented_type": "float"}
    if isinstance(ValueData, (date, datetime)):
        return {"date": ValueData.isoformat()}
    if isinstance(ValueData, (tuple, list)):
        return [PlainValue(EntryData) for EntryData in ValueData]
    return {"unrepresented_type": type(ValueData).__name__}


# machine paths and traceback text must not leak into distributable metadata
def ErrorValue(ErrorData):
    return {
        "error_type": type(ErrorData).__name__,
        "hresult": getattr(ErrorData, "hresult", None),
    }


# library versions and locales prevent unrelated declarations from sharing identities
def LibraryKey(LibraryData):
    AttrData = LibraryData.GetLibAttr()
    return f"library:{AttrData[0]}:{AttrData[3]}.{AttrData[4]}:{AttrData[1]}"


# references use declaration identities rather than unstable local handle values
def TypeKey(TypeInfo):
    LibraryData, TypeIndex = TypeInfo.GetContainingTypeLib()
    return LibraryKey(LibraryData) + "/" + TypeInfo.GetDocumentation(-1)[0]


# recursive signatures preserve pointers arrays and declared interface references
def ReadTypeValue(TypeInfo, TypeData):
    if not isinstance(TypeData, tuple):
        return {"vartype": int(TypeData)}
    TypeCode, DetailData = TypeData
    ResultData = {"vartype": int(TypeCode)}
    if TypeCode == 29:
        RefInfo = TypeInfo.GetRefTypeInfo(DetailData)
        ResultData.update(
            reference=RefInfo.GetDocumentation(-1)[0],
            reference_id=TypeKey(RefInfo),
            guid=str(RefInfo.GetTypeAttr().iid),
        )
    elif TypeCode in (26, 27):
        ResultData["element"] = ReadTypeValue(TypeInfo, DetailData)
    else:
        ResultData["detail"] = PlainValue(DetailData)
    return ResultData


# accessors remain distinct because merged names would erase write semantics
def ReadFunction(TypeInfo, DescData, OwnerId):
    MemberNames = TypeInfo.GetNames(DescData.memid)
    ParamData = []
    for Index, ArgData in enumerate(DescData.args):
        ParamData.append(
            {
                "name": (
                    MemberNames[Index + 1]
                    if Index + 1 < len(MemberNames)
                    else f"argument{Index + 1}"
                ),
                "name_observed": Index + 1 < len(MemberNames),
                "ordinal": Index,
                "type": ReadTypeValue(TypeInfo, ArgData[0]),
                "flags": int(ArgData[1]),
                "has_default": bool(ArgData[1] & 32),
                "default": PlainValue(ArgData[2]),
            }
        )
    return {
        "id": f"{OwnerId}/{DescData.memid}/{DescData.invkind}",
        "name": MemberNames[0],
        "memid": int(DescData.memid),
        "invkind": int(DescData.invkind),
        "flags": int(DescData.wFuncFlags),
        "function_kind": int(DescData.funckind),
        "calling_convention": int(DescData.callconv),
        "return_type": ReadTypeValue(TypeInfo, DescData.rettype[0]),
        "return_flags": int(DescData.rettype[1]),
        "optional_count": int(DescData.cParamsOpt),
        "parameters": ParamData,
    }


# declared variables distinguish enum constants from instance storage descriptors
def ReadVariable(TypeInfo, DescData, OwnerId, IsCommand):
    return {
        "id": f"{OwnerId}/{DescData.memid}",
        "name": TypeInfo.GetDocumentation(DescData.memid)[0],
        "memid": int(DescData.memid),
        "kind": int(DescData.varkind),
        "flags": int(DescData.wVarFlags),
        "type": ReadTypeValue(TypeInfo, DescData.elemdescVar[0]),
        "type_flags": int(DescData.elemdescVar[1]),
        "value": PlainValue(DescData.value) if DescData.varkind == 2 else None,
        "storage_offset": PlainValue(DescData.value) if DescData.varkind == 0 else None,
        "command_candidate": IsCommand and DescData.varkind == 2,
    }


# each descriptor failure must stay visible without discarding unrelated declarations
def ReadTypeInfo(TypeInfo, IsCommand):
    AttrData = TypeInfo.GetTypeAttr()
    OwnerId = TypeKey(TypeInfo)
    ResultData = {
        "id": OwnerId,
        "name": TypeInfo.GetDocumentation(-1)[0],
        "kind": int(AttrData.typekind),
        "guid": str(AttrData.iid),
        "flags": int(AttrData.wTypeFlags),
        "declared_function_count": int(AttrData.cFuncs),
        "declared_variable_count": int(AttrData.cVars),
        "declared_base_count": int(AttrData.cImplTypes),
        "bases": [],
        "functions": [],
        "variables": [],
        "errors": [],
    }
    if AttrData.typekind == 6:
        ResultData["alias_type"] = ReadTypeValue(TypeInfo, AttrData.tdescAlias)
    for Index in range(AttrData.cImplTypes):
        try:
            RefInfo = TypeInfo.GetRefTypeInfo(TypeInfo.GetRefTypeOfImplType(Index))
            ResultData["bases"].append(
                {
                    "id": TypeKey(RefInfo),
                    "name": RefInfo.GetDocumentation(-1)[0],
                    "flags": int(TypeInfo.GetImplTypeFlags(Index)),
                }
            )
        except Exception as ErrorData:
            ResultData["errors"].append({"base_index": Index, **ErrorValue(ErrorData)})
    for Index in range(AttrData.cFuncs):
        try:
            ResultData["functions"].append(
                ReadFunction(TypeInfo, TypeInfo.GetFuncDesc(Index), OwnerId)
            )
        except Exception as ErrorData:
            ResultData["errors"].append(
                {"function_index": Index, **ErrorValue(ErrorData)}
            )
    for Index in range(AttrData.cVars):
        try:
            ResultData["variables"].append(
                ReadVariable(TypeInfo, TypeInfo.GetVarDesc(Index), OwnerId, IsCommand)
            )
        except Exception as ErrorData:
            ResultData["errors"].append(
                {"variable_index": Index, **ErrorValue(ErrorData)}
            )
    return ResultData


# fingerprints bind declarations to installed bytes without distributing vendor libraries
def ReadLibrary(SourcePath, SourceLeaf):
    SourceHash = sha256(SourcePath.read_bytes()).hexdigest()
    LibraryData = LoadComLibrary(SourcePath)
    AttrData = LibraryData.GetLibAttr()
    ResultData = {
        "id": LibraryKey(LibraryData),
        "name": LibraryData.GetDocumentation(-1)[0],
        "guid": str(AttrData[0]),
        "major": int(AttrData[3]),
        "minor": int(AttrData[4]),
        "locale": int(AttrData[1]),
        "source_sha256": SourceHash,
        "source_leaf": SourceLeaf,
        "declared_type_count": int(LibraryData.GetTypeInfoCount()),
        "types": [],
        "errors": [],
    }
    IsCommand = "command" in ResultData["name"].lower()
    for Index in range(ResultData["declared_type_count"]):
        try:
            ResultData["types"].append(
                ReadTypeInfo(LibraryData.GetTypeInfo(Index), IsCommand)
            )
        except Exception as ErrorData:
            ResultData["errors"].append({"type_index": Index, **ErrorValue(ErrorData)})
    if sha256(SourcePath.read_bytes()).hexdigest() != SourceHash:
        raise ValueError("Type library changed during collection")
    return ResultData


# explicit registration flags avoid legacy loader registration side effects
def LoadComLibrary(SourcePath):
    from ctypes import OleDLL, POINTER, WINFUNCTYPE, byref, c_int, c_ulong
    from ctypes import c_void_p, c_wchar_p, cast
    from pythoncom import IID_ITypeLib, ObjectFromAddress

    LoadLibrary = OleDLL("oleaut32").LoadTypeLibEx
    LoadLibrary.argtypes = [c_wchar_p, c_int, POINTER(c_void_p)]
    LoadLibrary.restype = c_int
    LibraryPtr = c_void_p()
    LoadLibrary(str(SourcePath), 2, byref(LibraryPtr))
    try:
        return ObjectFromAddress(LibraryPtr.value, IID_ITypeLib)
    finally:
        VtablePtr = cast(LibraryPtr, POINTER(POINTER(c_void_p))).contents
        ReleaseRef = WINFUNCTYPE(c_ulong, c_void_p)(VtablePtr[2])
        ReleaseRef(LibraryPtr)


# scanning metadata never attaches to user sessions or registers type libraries
def CollectApi(InstallRoot):
    from win32api import GetFileVersionInfo, HIWORD, LOWORD

    RootPath = Path(InstallRoot).resolve(strict=True)
    Libraries, Errors, SeenSources, SourceFiles = [], [], {}, []
    SourcePaths = sorted(RootPath.rglob("*.tlb"))
    if not SourcePaths:
        raise ValueError("No type libraries found in installation root")
    for SourcePath in SourcePaths:
        SourceLeaf = SourcePath.relative_to(RootPath).as_posix()
        try:
            SourceHash = sha256(SourcePath.read_bytes()).hexdigest()
            SourceFiles.append({"leaf": SourceLeaf, "sha256": SourceHash})
            if SourceHash in SeenSources:
                SourceFiles[-1]["duplicate_of"] = SeenSources[SourceHash]
                continue
            SeenSources[SourceHash] = SourceLeaf
            Libraries.append(ReadLibrary(SourcePath, SourceLeaf))
        except Exception as ErrorData:
            Errors.append({"source_leaf": SourceLeaf, **ErrorValue(ErrorData)})
    VersionData, ExeHash = None, None
    ExePath = RootPath / "SLDWORKS.exe"
    if ExePath.is_file():
        try:
            ExeHash = sha256(ExePath.read_bytes()).hexdigest()
            FileInfo = GetFileVersionInfo(str(ExePath), "\\")
            VersionData = ".".join(
                str(PartValue)
                for PartValue in (
                    HIWORD(FileInfo["FileVersionMS"]),
                    LOWORD(FileInfo["FileVersionMS"]),
                    HIWORD(FileInfo["FileVersionLS"]),
                    LOWORD(FileInfo["FileVersionLS"]),
                )
            )
        except Exception as ErrorData:
            Errors.append({"source_leaf": "SLDWORKS.exe", **ErrorValue(ErrorData)})
    return {
        "_notice": KNoticeText,
        "schema_version": 1,
        "collection": {
            "mode": "LoadTypeLibEx(REGKIND_NONE)",
            "installation_version": VersionData,
            "executable_sha256": ExeHash,
            "source_scope": "recursive installed root tlb files",
            "source_files": SourceFiles,
            "source_file_count": len(SourcePaths),
            "cad_application_launched": False,
            "registration_requested": False,
            "availability": "unverified",
            "native_serialization": "unverified",
        },
        "libraries": Libraries,
        "errors": Errors,
    }


# exclusive publication protects snapshots already owned by users or earlier research
def MainEntry():
    ParserData = ArgumentParser(
        description="Read installed SOLIDWORKS COM declarations"
    )
    ParserData.add_argument("--install-root", required=True, type=Path)
    ParserData.add_argument("--output", required=True, type=Path)
    ArgsData = ParserData.parse_args()
    if ArgsData.output.exists():
        raise FileExistsError("Output snapshot already exists")
    SnapshotData = CollectApi(ArgsData.install_root)
    ArgsData.output.parent.mkdir(parents=True, exist_ok=True)
    with ArgsData.output.open("x", encoding="utf-8", newline="\n") as OutputFile:
        OutputFile.write(
            dumps(SnapshotData, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n"
        )
    print(
        dumps(
            {
                "libraries": len(SnapshotData["libraries"]),
                "source_files": SnapshotData["collection"]["source_file_count"],
                "load_errors": len(SnapshotData["errors"]),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    MainEntry()
