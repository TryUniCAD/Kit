from __future__ import annotations

import os
from AuthorCurves import require

LIBRARIES={"sldworks":"{83A33D31-27C5-11CE-BFD4-00400513BB57}","swconst":"{4687F359-55D0-4CD3-B6CF-2EB42C11F989}"}
MEMBERS={
 "IAssemblyDoc":("AddMate5","AddComponents3","FixComponent","UnfixComponent","GetComponents","GetComponentCount"),
 "IComponent2":("GetID","Name2","Transform2","SetTransformAndSolve2","GetCorrespondingEntity","GetModelDoc2","GetPathName","ReferencedConfiguration","IsFixed","IsSuppressed","Select4"),
 "IMate2":("Type","Alignment","GetMateEntityCount","MateEntity"),
 "IMateEntity2":("ReferenceComponent","ReferenceType2","Reference","EntityParams","GetEntityParamsSize"),
 "IConcentricMateFeatureData":("LockRotation",),
 "IFeature":("GetID","Name","GetTypeName2","GetSpecificFeature2","GetDefinition","GetFirstDisplayDimension","GetErrorCode2"),
 "IModelDoc2":("Parameter","ForceRebuild3","SetSaveFlag","Save3","GetUpdateStamp"),
 "IModelDocExtension":("GetWhatsWrongCount","GetPersistReference3"),
 "IPartDoc":("GetBodies2","FeatureByName"),
 "IBody2":("GetFaces",),
 "IFace2":("GetSurface",),
 "ISurface":("IsCylinder","CylinderParams"),
 "IEntity":("Select4","GetComponent"),
 "ISelectionMgr":("CreateSelectData",),
 "ISelectData":("Mark",),
 "IDimension":("SystemValue","SetSystemValue3","DrivenState","ReadOnly","FullName"),
 "IMathUtility":("CreateTransform",),
 "IMathTransform":("ArrayData",),
 "ISldWorks":("IsSame","GetMathUtility",),
}
ENUMS={"swMateType_e":("swMateCONCENTRIC",),"swMateAlign_e":("swMateAlignALIGNED","swMateAlignANTI_ALIGNED"),"swAddMateError_e":("swAddMateError_NoError",),"swSelectType_e":("swSelFACES",),"swObjectEquality":("swObjectSame","swObjectNotSame","swObjectUnsupported")}


def metadata():
    require(os.name=="nt","registered concentric metadata runs only in the guest")
    import pythoncom
    pythoncom.CoInitialize()
    try:
        libraries={key:pythoncom.LoadRegTypeLib(value,34,0,0) for key,value in LIBRARIES.items()}
        require(all(tuple(value.GetLibAttr()[3:5])==(34,0) for value in libraries.values()),"both exact 2026 type libraries are required")
        interfaces,enums={},{}
        for library_name,library in libraries.items():
            for index in range(library.GetTypeInfoCount()):
                info=library.GetTypeInfo(index)
                name=info.GetDocumentation(-1)[0]
                attributes=info.GetTypeAttr()
                if library_name=="sldworks" and name in MEMBERS:
                    rows=[]
                    for ordinal in range(attributes.cFuncs):
                        descriptor=info.GetFuncDesc(ordinal)
                        names=list(info.GetNames(descriptor.memid))
                        if names and (names[0] in MEMBERS[name] or name=="IConcentricMateFeatureData"):
                            rows.append({"names":names,"member_id":descriptor.memid,"invoke_kind":descriptor.invkind,"arguments":repr(descriptor.args),"return_type":repr(descriptor.rettype)})
                    interfaces[name]={"guid":str(attributes[0]),"members":rows}
                if library_name=="swconst" and name in ENUMS:
                    values={}
                    for ordinal in range(attributes.cVars):
                        descriptor=info.GetVarDesc(ordinal)
                        member=info.GetNames(descriptor.memid)[0]
                        if member in ENUMS[name]: values[member]=descriptor.value
                    enums[name]=values
        for name,methods in MEMBERS.items():
            require(name in interfaces and all(any(row["names"][0]==method for row in interfaces[name]["members"]) for method in methods),"registered concentric prerequisite missing in "+name)
        for name,members in ENUMS.items(): require(name in enums and set(enums[name])==set(members),"concentric enum metadata is incomplete")
        require(enums["swMateType_e"]["swMateCONCENTRIC"]==1 and enums["swMateAlign_e"]=={"swMateAlignALIGNED":0,"swMateAlignANTI_ALIGNED":1} and enums["swAddMateError_e"]["swAddMateError_NoError"]==1 and enums["swSelectType_e"]["swSelFACES"]==2,"registered concentric enum declarations differ")
        signatures={row["names"][0]:row for row in interfaces["IAssemblyDoc"]["members"]}
        require(len(signatures["AddMate5"]["names"])==16 and len(signatures["AddComponents3"]["names"])==4,"assembly method signatures differ")
        getter=[row for row in interfaces["IConcentricMateFeatureData"]["members"] if row["names"][0]=="LockRotation" and row["invoke_kind"]==2]
        require(len(getter)==1 and getter[0]["return_type"].startswith("(11,"),"concentric rotation lock needs its registered Boolean getter")
        return {"schema":"kit.sw2026.concentric-api-metadata.v1","interfaces":interfaces,"enums":enums,"libraries":{key:{"guid":str(value.GetLibAttr()[0]),"major":value.GetLibAttr()[3],"minor":value.GetLibAttr()[4]} for key,value in libraries.items()},"native_processes_started":0,"passed":True}
    finally:
        pythoncom.CoUninitialize()
