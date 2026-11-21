from FilletModel import require

MODEL_LIB = "{83A33D31-27C5-11CE-BFD4-00400513BB57}"
CONSTS_LIB = "{4687F359-55D0-4CD3-B6CF-2EB42C11F989}"
ENUMS = {
    "swFeatureNameID_e": ("swFmFillet",),
    "swSimpleFilletType_e": ("swConstRadiusFillet",),
    "swFeatureFilletProfileType_e": ("swFeatureFilletCircular",),
    "swSelectType_e": ("swSelEDGES",),
    "swBodyType_e": ("swSolidBody", "swSheetBody"),
    "swEndConditions_e": ("swEndCondBlind",),
    "swDimensionType_e": ("swRadialDimension",),
    "swDimensionDrivenState_e": ("swDimensionDriving",),
    "swSetValueInConfiguration_e": ("swSetValue_InThisConfiguration",),
    "swSetValueReturnStatus_e": ("swSetValue_Successful",),
    "swObjectEquality": ("swObjectSame",),
    "swUserPreferenceToggle_e": ("swDisplayFeatureDimensions",),
}
FLAGS = ("PropagateToTangentFaces", "IsMultipleRadius", "AsymmetricFillet", "RoundCorners",
         "EnablePartialEdgeParameters", "CurvatureContinuous", "ConstantWidth")
FEATURE_DATA = (
    "Initialize", "Type", "ConicTypeForCrossSectionProfile", "DefaultRadius", "Edges", "GetEdgeCount",
    "FilletItemsCount", "GetFilletItemAtIndex", "AccessSelections", "ReleaseSelectionAccess", "Features", "Loops",
    *FLAGS,
)
MEMBERS = {
    "IFeatureManager": ("CreateDefinition", "CreateFeature", "FeatureExtrusion3"),
    "ISimpleFilletFeatureData2": FEATURE_DATA,
    "IModelDocExtension": ("GetPersistReference3", "GetWhatsWrongCount"),
    "IBody2": ("GetEdges", "GetFaces", "GetVertices", "GetExtremePoint"),
    "IEdge": ("GetStartVertex", "GetEndVertex", "GetCurve", "GetTwoAdjacentFaces2"),
    "IEntity": ("Select4",),
    "ISelectData": ("Mark",),
    "ISelectionMgr": ("CreateSelectData", "GetSelectedObject6", "GetSelectedObjectCount2", "GetSelectedObjectType3"),
    "IFace2": ("GetBody", "GetFeature", "GetSurface"),
    "ISurface": ("IsPlane", "IsCylinder", "CylinderParams"),
    "IFeature": ("GetDefinition", "GetFaces", "GetParents", "GetFirstDisplayDimension", "GetNextDisplayDimension"),
    "IDisplayDimension": ("GetDimension2", "Type2"),
    "IDimension": ("FullName", "ReadOnly", "DrivenState", "SystemValue", "SetSystemValue3"),
}


def load(sw, guid):
    library = sw.pythoncom.LoadRegTypeLib(guid, 34, 0, 0)
    attributes = library.GetLibAttr()
    require(str(attributes[0]).casefold() == guid.casefold() and attributes[3:5] == (34, 0),
            "incorrect registered SOLIDWORKS API library")
    return library, {"guid": str(attributes[0]), "locale_id": attributes[1], "system_kind": attributes[2],
                     "version": list(attributes[3:5])}


def installed_registration(sw):
    library, model_id = load(sw, MODEL_LIB)
    found = {}
    for index in range(library.GetTypeInfoCount()):
        name = library.GetDocumentation(index)[0]
        if name not in MEMBERS:
            continue
        info = library.GetTypeInfo(index)
        signatures = {}
        for offset in range(info.GetTypeAttr().cFuncs):
            member = info.GetFuncDesc(offset)
            names = info.GetNames(member.memid)
            if names and names[0] in MEMBERS[name]:
                signatures.setdefault(names[0], []).append({"member_id": member.memid, "invoke_kind": member.invkind,
                       "names": list(names), "arguments": repr(member.args), "return": repr(member.rettype)})
        require(set(signatures) == set(MEMBERS[name]),
                f"registered {name} is missing members {sorted(set(MEMBERS[name]) - signatures.keys())}")
        found[name] = signatures
    require(found.keys() == MEMBERS.keys(), "installed SOLIDWORKS fillet interface inventory is incomplete")
    library, constants_id = load(sw, CONSTS_LIB)
    enums = {}
    for index in range(library.GetTypeInfoCount()):
        name = library.GetDocumentation(index)[0]
        if name in ENUMS:
            info = library.GetTypeInfo(index)
            values = [info.GetVarDesc(offset) for offset in range(info.GetTypeAttr().cVars)]
            enums[name] = {info.GetNames(member.memid)[0]: member.value for member in values}
    require(all(name in enums and all(type(enums[name].get(member)) is int for member in members)
                for name, members in ENUMS.items()), "registered SOLIDWORKS fillet enum inventory is incomplete")
    constants = {member: enums[name][member] for name, members in ENUMS.items() for member in members}
    return constants, {"model_library": model_id, "constants_library": constants_id,
                       "interfaces": found, "constants": constants}
