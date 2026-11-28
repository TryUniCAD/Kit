from __future__ import annotations

import os

from AuthorCurves import require

LIBRARIES = {
    "sldworks": "{83A33D31-27C5-11CE-BFD4-00400513BB57}",
    "swconst": "{4687F359-55D0-4CD3-B6CF-2EB42C11F989}",
}
MEMBERS = {
    "IFeatureManager": ("FeatureExtrusion3", "FeatureCut4"),
    "IExtrudeFeatureData2": (
        "GetDepth",
        "GetEndCondition",
        "BothDirections",
        "ReverseDirection",
        "FromType",
        "IsThinFeature",
        "GetDraftWhileExtruding",
        "FlipSideToCut",
        "NormalCut",
    ),
    "IModelDoc2": (
        "Parameter",
        "ForceRebuild3",
        "FeatureByPositionReverse",
        "ClearSelection2",
        "FirstFeature",
    ),
    "IPartDoc": ("FeatureByName",),
    "IFeature": (
        "GetDefinition",
        "GetFirstDisplayDimension",
        "GetNextDisplayDimension",
        "GetSpecificFeature2",
        "GetParents",
        "Select2",
    ),
    "IDisplayDimension": ("GetDimension2",),
    "IDimension": (
        "SystemValue",
        "FullName",
        "ReadOnly",
        "DrivenState",
        "SetSystemValue3",
    ),
    "ISketchManager": (
        "CreateCornerRectangle",
        "CreateCircleByRadius",
        "InsertSketch",
        "ActiveSketch",
        "AddToDB",
    ),
    "ISketch": ("ModelToSketchTransform", "GetSketchSegments"),
}
ENUMS = {
    "swEndConditions_e": {
        "swEndCondBlind": 0,
        "swEndCondThroughAll": 1,
        "swEndCondMidPlane": 6,
        "swEndCondThroughAllBoth": 9,
    }
}
BOSS_ARGUMENTS = (
    "Sd",
    "Flip",
    "Dir",
    "T1",
    "T2",
    "D1",
    "D2",
    "Dchk1",
    "Dchk2",
    "Ddir1",
    "Ddir2",
    "Dang1",
    "Dang2",
    "OffsetReverse1",
    "OffsetReverse2",
    "TranslateSurface1",
    "TranslateSurface2",
    "Merge",
    "UseFeatScope",
    "UseAutoSelect",
    "T0",
    "StartOffset",
    "FlipStartOffset",
)
CUT_ARGUMENTS = (
    "Sd",
    "Flip",
    "Dir",
    "T1",
    "T2",
    "D1",
    "D2",
    "Dchk1",
    "Dchk2",
    "Ddir1",
    "Ddir2",
    "Dang1",
    "Dang2",
    "OffsetReverse1",
    "OffsetReverse2",
    "TranslateSurface1",
    "TranslateSurface2",
    "NormalCut",
    "UseFeatScope",
    "UseAutoSelect",
    "AssemblyFeatureScope",
    "AutoSelectComponents",
    "PropagateFeatureToParts",
    "T0",
    "StartOffset",
    "FlipStartOffset",
    "OptimizeGeometry",
)


def metadata():
    require(
        os.name == "nt",
        "registered through-all API metadata is inspected only inside the guest",
    )
    import pythoncom

    pythoncom.CoInitialize()
    try:
        libraries = {
            name: pythoncom.LoadRegTypeLib(identity, 34, 0, 0)
            for name, identity in LIBRARIES.items()
        }
        require(
            all(
                tuple(library.GetLibAttr()[3:5]) == (34, 0)
                for library in libraries.values()
            ),
            "use both pinned 2026 type libraries",
        )
        interfaces, enums = {}, {}
        for kind, library in libraries.items():
            for ordinal in range(library.GetTypeInfoCount()):
                info = library.GetTypeInfo(ordinal)
                name = info.GetDocumentation(-1)[0]
                attr = info.GetTypeAttr()
                if kind == "sldworks" and name in MEMBERS:
                    rows = []
                    for index in range(attr.cFuncs):
                        desc = info.GetFuncDesc(index)
                        names = list(info.GetNames(desc.memid))
                        if names and names[0] in MEMBERS[name]:
                            rows.append(
                                {
                                    "names": names,
                                    "member_id": desc.memid,
                                    "invoke_kind": desc.invkind,
                                    "arguments": repr(desc.args),
                                    "return_type": repr(desc.rettype),
                                }
                            )
                    interfaces[name] = {"guid": str(attr[0]), "members": rows}
                if kind == "swconst" and name in ENUMS:
                    values = {}
                    for index in range(attr.cVars):
                        desc = info.GetVarDesc(index)
                        item = info.GetNames(desc.memid)[0]
                        if item in ENUMS[name]:
                            values[item] = desc.value
                    enums[name] = values
        for name, members in MEMBERS.items():
            require(
                name in interfaces
                and all(
                    any(row["names"][0] == item for row in interfaces[name]["members"])
                    for item in members
                ),
                f"the registered through-all API lacks a prerequisite in {name}",
            )
        require(enums == ENUMS, "the pinned through-all enum declaration differs")
        signatures = {
            row["names"][0]: row for row in interfaces["IFeatureManager"]["members"]
        }
        for name, wanted in (
            ("FeatureExtrusion3", BOSS_ARGUMENTS),
            ("FeatureCut4", CUT_ARGUMENTS),
        ):
            require(
                tuple(value.casefold() for value in signatures[name]["names"][1:])
                == tuple(value.casefold() for value in wanted),
                f"the registered {name} parameter order differs",
            )
        return {
            "schema": "kit.sw2026.through-all-api-metadata.v1",
            "interfaces": interfaces,
            "enums": enums,
            "libraries": {
                name: {"guid": str(library.GetLibAttr()[0]), "major": 34, "minor": 0}
                for name, library in libraries.items()
            },
            "native_processes_started": 0,
            "passed": True,
        }
    finally:
        pythoncom.CoUninitialize()
