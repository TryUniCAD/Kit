from __future__ import annotations

import os

from AuthorCurves import require


LIBRARIES = {"sldworks": "{83A33D31-27C5-11CE-BFD4-00400513BB57}", "swconst": "{4687F359-55D0-4CD3-B6CF-2EB42C11F989}"}
MEMBERS = {
    "IAssemblyDoc": ("AddMate5", "AddComponents3", "FixComponent", "UnfixComponent", "GetComponents", "GetComponentCount"),
    "IComponent2": ("GetID", "Name2", "Transform2", "SetTransformAndSolve2", "FeatureByName", "GetModelDoc2", "GetPathName", "ReferencedConfiguration", "IsFixed", "IsSuppressed"),
    "IMate2": ("Type", "Alignment", "GetMateEntityCount", "MateEntity"),
    "IMateEntity2": ("ReferenceComponent", "ReferenceType2", "Reference", "EntityParams"),
    "IFeature": ("GetID", "Name", "GetTypeName2", "GetSpecificFeature2", "GetFirstDisplayDimension"),
    "IModelDoc2": ("Parameter", "ForceRebuild3", "SetSaveFlag", "Save3", "GetUpdateStamp"),
    "IDimension": ("SystemValue", "SetSystemValue3", "DrivenState", "ReadOnly", "FullName"),
    "IMathUtility": ("CreateTransform",),
    "IMathTransform": ("ArrayData",),
    "ISldWorks": ("IsSame", "GetMathUtility"),
}
ENUMS = {"swMateType_e": ("swMatePERPENDICULAR",), "swMateAlign_e": ("swMateAlignALIGNED",),
         "swAddMateError_e": ("swAddMateError_NoError",), "swObjectEquality": ("swObjectSame", "swObjectNotSame", "swObjectUnsupported")}


def metadata():
    require(os.name == "nt", "registered perpendicular API metadata is inspected only inside the guest")
    import pythoncom

    pythoncom.CoInitialize()
    try:
        libraries = {name: pythoncom.LoadRegTypeLib(identity, 34, 0, 0) for name, identity in LIBRARIES.items()}
        require(all(tuple(library.GetLibAttr()[3:5]) == (34, 0) for library in libraries.values()), "use both exact 2026 type libraries")
        interfaces, enums = {}, {}
        for library_name, library in libraries.items():
            for index in range(library.GetTypeInfoCount()):
                info = library.GetTypeInfo(index)
                name = info.GetDocumentation(-1)[0]
                attributes = info.GetTypeAttr()
                if library_name == "sldworks" and name in MEMBERS:
                    selected = []
                    for ordinal in range(attributes.cFuncs):
                        descriptor = info.GetFuncDesc(ordinal)
                        names = list(info.GetNames(descriptor.memid))
                        if names and names[0] in MEMBERS[name]:
                            selected.append({"names": names, "member_id": descriptor.memid, "invoke_kind": descriptor.invkind,
                                             "arguments": repr(descriptor.args), "return_type": repr(descriptor.rettype)})
                    interfaces[name] = {"guid": str(attributes[0]), "members": selected}
                if library_name == "swconst" and name in ENUMS:
                    values = {}
                    for ordinal in range(attributes.cVars):
                        descriptor = info.GetVarDesc(ordinal)
                        value_name = info.GetNames(descriptor.memid)[0]
                        if value_name in ENUMS[name]:
                            require(type(descriptor.value) is int, "the native mate declaration is not an integer enum")
                            values[value_name] = descriptor.value
                    enums[name] = values
        for name, members in MEMBERS.items():
            require(name in interfaces and all(any(row["names"][0] == method for row in interfaces[name]["members"]) for method in members),
                    f"the registered perpendicular API lacks a declared prerequisite in {name}")
        for name, members in ENUMS.items():
            require(name in enums and set(enums[name]) == set(members), "the perpendicular enum declaration is incomplete")
        require(enums["swMateType_e"]["swMatePERPENDICULAR"] == 2 and enums["swMateAlign_e"]["swMateAlignALIGNED"] == 0
                and enums["swAddMateError_e"]["swAddMateError_NoError"] == 1, "the pinned perpendicular API enum differs")
        signatures = {row["names"][0]: row for row in interfaces["IAssemblyDoc"]["members"]}
        require(len(signatures["AddMate5"]["names"]) == 16 and len(signatures["AddComponents3"]["names"]) == 4,
                "the native author method argument counts differ")
        return {"schema": "kit.sw2026.perpendicular-api-metadata.v1", "interfaces": interfaces, "enums": enums,
                "libraries": {name: {"guid": str(value.GetLibAttr()[0]), "major": value.GetLibAttr()[3], "minor": value.GetLibAttr()[4]}
                              for name, value in libraries.items()}, "native_processes_started": 0, "passed": True}
    finally:
        pythoncom.CoUninitialize()
