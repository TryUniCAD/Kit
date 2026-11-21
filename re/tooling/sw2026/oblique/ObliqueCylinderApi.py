import os

from ObliqueCylinderPlan import require

LIBRARIES = {
    "sldworks": "{83A33D31-27C5-11CE-BFD4-00400513BB57}",
    "swconst": "{4687F359-55D0-4CD3-B6CF-2EB42C11F989}",
}
MEMBERS = {
    "IFeatureManager": ("InsertRefPlane", "FeatureExtrusion3"),
    "IModelDoc2": (
        "InsertAxis2",
        "Parameter",
        "ForceRebuild3",
        "ClearSelection2",
        "FirstFeature",
        "AddRadialDimension2",
    ),
    "IPartDoc": ("FeatureByName", "GetBodies2"),
    "IFeature": (
        "Name",
        "GetTypeName2",
        "GetNextFeature",
        "GetFirstDisplayDimension",
        "GetNextDisplayDimension",
        "GetSpecificFeature2",
        "GetDefinition",
        "GetParents",
        "Select2",
    ),
    "IRefPlaneFeatureData": (
        "Reference",
        "Constraint",
        "AngleOrDistance",
        "AccessSelections",
        "ReleaseSelectionAccess",
        "Type",
        "Type2",
    ),
    "IRefPlane": ("Transform",),
    "IRefAxis": ("GetRefAxisParams",),
    "ISelectionMgr": (
        "GetSelectedObjectCount2",
        "GetSelectedObject6",
        "GetSelectedObjectMark",
        "GetSelectedObjectType3",
    ),
    "IDimension": (
        "FullName",
        "SystemValue",
        "DrivenState",
        "ReadOnly",
        "SetSystemValue3",
    ),
    "IDisplayDimension": ("GetDimension2", "Type2"),
    "ISketchManager": (
        "InsertSketch",
        "ActiveSketch",
        "AddToDB",
        "CreateCircleByRadius",
    ),
    "ISketch": ("GetSketchSegments", "ModelToSketchTransform"),
    "IExtrudeFeatureData2": (
        "AccessSelections",
        "ReleaseSelectionAccess",
        "GetDirectionReference",
        "GetEndCondition",
        "GetEndConditionReference",
        "GetDepth",
        "BothDirections",
        "ReverseDirection",
        "IsThinFeature",
        "GetDraftWhileExtruding",
        "FromType",
    ),
    "ISldWorks": ("IsSame", "GetMathUtility"),
    "IMathUtility": ("CreatePoint", "CreateVector"),
    "IMathPoint": ("MultiplyTransform", "ArrayData"),
    "IMathVector": ("MultiplyTransform", "ArrayData"),
    "IMathTransform": ("ArrayData",),
}
ENUMS = {
    "swRefPlaneReferenceConstraints_e": (
        "swRefPlaneReferenceConstraint_Angle",
        "swRefPlaneReferenceConstraint_Coincident",
        "swRefPlaneReferenceConstraint_Distance",
        "swRefPlaneReferenceConstraint_OptionFlip",
    ),
    "swDimensionType_e": (
        "swAngularDimension",
        "swRadialDimension",
        "swLinearDimension",
    ),
    "swSelectType_e": ("swSelDATUMPLANES", "swSelDATUMAXES", "swSelSKETCHES"),
    "swObjectEquality": ("swObjectSame", "swObjectNotSame", "swObjectUnsupported"),
    "swEndConditions_e": (
        "swEndCondBlind",
        "swEndCondUpToSurface",
        "swEndCondUpToSelection",
    ),
}
INSERT_ARGUMENTS = (
    "FirstConstraint",
    "FirstConstraintAngleOrDistance",
    "SecondConstraint",
    "SecondConstraintAngleOrDistance",
    "ThirdConstraint",
    "ThirdConstraintAngleOrDistance",
)
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


def metadata():
    require(os.name == "nt", "registered oblique API metadata runs only in the guest")
    import inspect
    import pythoncom
    import win32com.client as wc

    pythoncom.CoInitialize()
    try:
        libraries = {
            name: pythoncom.LoadRegTypeLib(value, 34, 0, 0)
            for name, value in LIBRARIES.items()
        }
        require(
            all(
                tuple(value.GetLibAttr()[3:5]) == (34, 0)
                for value in libraries.values()
            ),
            "both registered libraries must be 34.0",
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
                                    "argument_count": len(desc.args),
                                }
                            )
                    interfaces[name] = {"guid": str(attr[0]), "members": rows}
                if kind == "swconst" and name in ENUMS:
                    values = {}
                    for index in range(attr.cVars):
                        desc = info.GetVarDesc(index)
                        member = info.GetNames(desc.memid)[0]
                        if member in ENUMS[name]:
                            values[member] = desc.value
                    enums[name] = values
        for name, wanted in MEMBERS.items():
            require(name in interfaces, "missing registered oblique interface " + name)
            actual = {row["names"][0] for row in interfaces[name]["members"]}
            require(
                set(wanted) <= actual,
                "missing registered oblique members in "
                + name
                + ": "
                + repr(sorted(set(wanted) - actual)),
            )
        for name, wanted in ENUMS.items():
            require(
                name in enums and set(enums[name]) == set(wanted),
                "missing registered oblique enum " + name,
            )
        for interface, method, names in (
            ("IFeatureManager", "InsertRefPlane", INSERT_ARGUMENTS),
            ("IFeatureManager", "FeatureExtrusion3", BOSS_ARGUMENTS),
            ("IModelDoc2", "InsertAxis2", ("AutoSize",)),
        ):
            (selected,) = [
                row
                for row in interfaces[interface]["members"]
                if row["names"][0] == method and row["invoke_kind"] == 1
            ]
            require(
                tuple(name.casefold() for name in selected["names"][1:])
                == tuple(name.casefold() for name in names),
                "registered call signature differs: " + method,
            )
        require(
            enums["swRefPlaneReferenceConstraints_e"]
            == {
                "swRefPlaneReferenceConstraint_Angle": 16,
                "swRefPlaneReferenceConstraint_Coincident": 4,
                "swRefPlaneReferenceConstraint_Distance": 8,
                "swRefPlaneReferenceConstraint_OptionFlip": 256,
            },
            "reference-plane flags differ",
        )
        require(
            enums["swEndConditions_e"]["swEndCondUpToSurface"] == 4
            and enums["swEndConditions_e"]["swEndCondUpToSelection"] == 10,
            "selected-end enum declarations differ",
        )
        generated = wc.gencache.EnsureModule(
            LIBRARIES["sldworks"], 0, 34, 0, bForDemand=False
        )
        typed = getattr(generated, "ExtrudeFeatureData2")
        typed = getattr(typed, "default_interface", typed)
        signatures = {
            name: [
                {
                    "name": value.name,
                    "kind": value.kind.name,
                    "has_default": value.default is not inspect.Parameter.empty,
                }
                for value in inspect.signature(getattr(typed, name)).parameters.values()
            ]
            for name in ("GetDirectionReference", "GetEndConditionReference")
        }
        return {
            "schema": "kit.sw2026.oblique-api-metadata.v1",
            "interfaces": interfaces,
            "enums": enums,
            "typed_python_signatures": signatures,
            "libraries": {
                name: {
                    "guid": str(value.GetLibAttr()[0]),
                    "major": value.GetLibAttr()[3],
                    "minor": value.GetLibAttr()[4],
                }
                for name, value in libraries.items()
            },
            "native_processes_started": 0,
            "passed": True,
        }
    finally:
        pythoncom.CoUninitialize()
