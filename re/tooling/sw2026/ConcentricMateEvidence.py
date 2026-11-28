from __future__ import annotations

from hashlib import sha256
from math import isclose,isfinite
from pathlib import Path

from AuthorCurves import require
from ConcentricSourcePlan import PARAMETERS,coaxial_residual,cross,dot,expected_transforms,geometry,norm,world


def same_file(value,expected):
    path=Path(str(value))
    return path.is_file() and path.samefile(expected)


def configuration(author,model,wanted):
    actual=str(author.get(author.get(model,"GetActiveConfiguration"),"Name"))
    require(list(author.get(model,"GetConfigurationNames") or ())==[wanted] and actual==wanted,"the source lost its exact active configuration")
    return actual


def component_map(author,assembly,case,expected_child):
    rows={}
    values=author.get(assembly,"GetComponents",True) or ()
    require(len(values)==int(author.get(assembly,"GetComponentCount",False))==2,"ordinary concentric source requires two direct resolved occurrences")
    for raw in values:
        component=author.typed(raw,"Component2")
        name=str(author.get(component,"Name2"))
        require(name in (case["child_name"]+"-1",case["child_name"]+"-2") and name not in rows and same_file(author.get(component,"GetPathName"),expected_child),"native occurrence name or child custody differs")
        rows[name]=component
    return [rows[case["child_name"]+"-"+str(index)] for index in (1,2)]


def local_cylinder(author,child,case):
    bodies=author.get(author.typed(child,"PartDoc"),"GetBodies2",0,True) or ()
    require(len(bodies)==1,"the native child must have one actual visible solid")
    faces=author.get(author.typed(bodies[0],"Body2"),"GetFaces") or ()
    candidates=[]
    for raw in faces:
        face=author.typed(raw,"Face2")
        surface=author.typed(author.get(face,"GetSurface"),"Surface")
        if bool(author.get(surface,"IsCylinder")):
            values=[float(value) for value in author.get(surface,"CylinderParams") or ()]
            require(len(values)==7 and all(map(isfinite,values)),"the native cylinder parameters are malformed")
            axis=values[3:6]
            require(isclose(norm(axis),1.0,abs_tol=1e-10) and abs(abs(axis[2])-1)<1e-10 and abs(axis[0])+abs(axis[1])<1e-10,"the source cylinder is not along its actual local sketch normal")
            delta=[values[0]-case["center_m"][0],values[1]-case["center_m"][1],values[2]]
            require(norm(cross(delta,axis))<1e-10 and isclose(values[6],case["radius_m"],rel_tol=1e-10,abs_tol=1e-12),"the selected cylinder does not have the authored local axis or radius")
            candidates.append((face,values))
    require(len(candidates)==1 and len(faces)==3,"the child must expose exactly its one cylinder and two caps")
    return candidates[0]


def author_mate(author,model,assembly,components,child,case):
    import Swapp
    for component in components:
        if author.get(component,"IsFixed"):
            author.get(model,"ClearSelection2",True)
            require(bool(author.get(component,"Select4",False,Swapp.nothing(),False)),"cannot select the initial fixed occurrence")
            author.get(assembly,"UnfixComponent")
    author.get(model,"ClearSelection2",True)
    require(bool(author.get(components[0],"Select4",False,Swapp.nothing(),False)),"cannot select the authored fixed anchor")
    author.get(assembly,"FixComponent")
    require(author.get(components[0],"IsFixed") and not author.get(components[1],"IsFixed"),"concentric source anchor state differs")
    face,_=local_cylinder(author,child,case)
    author.get(model,"ClearSelection2",True)
    manager=author.get(model,"SelectionManager")
    selected=[]
    for ordinal,index in enumerate(case["endpoint_order"]):
        specific=author.get(components[index],"GetCorrespondingEntity",face)
        require(specific is not None,"the actual cylinder cannot be resolved in its occurrence")
        entity=author.typed(specific,"Entity")
        owner=author.get(entity,"GetComponent")
        require(owner is not None and int(author.get(owner,"GetID"))==int(author.get(components[index],"GetID")),"selected cylinder belongs to a different occurrence")
        data=author.get(manager,"CreateSelectData")
        author.set(data,"Mark",1)
        require(bool(author.get(entity,"Select4",ordinal>0,data)),"concentric cylinder selection failed")
        selected.append({"occurrence":str(author.get(components[index],"Name2")),"occurrence_id":int(author.get(components[index],"GetID"))})
    status=Swapp.byref_long()
    mate=author.get(assembly,"AddMate5",1,case["api_alignment"],False,0.0,0.0,0.0,1.0,1.0,0.0,0.0,0.0,False,case["lock_rotation"],0,status)
    require(mate is not None and int(status.value)==1,"the native concentric API rejected its actual cylinder pair")
    from AssemblyMateEvidence import mate_features
    features=list(mate_features(author,model))
    require(len(features)==1,"the source API did not publish its one real mate")
    author.set(features[0],"Name",case["mate_name"])
    author.get(model,"ClearSelection2",True)
    return {"selected":selected,"api_status":int(status.value),"api_type":1,"api_alignment":case["api_alignment"],"lock_rotation":case["lock_rotation"]}


def object_evidence(author,model,reference,expected):
    import Swapp
    extension=author.get(model,"Extension")
    token=author.get(extension,"GetPersistReference3",reference)
    data=bytes(token or ())
    require(bool(data),"native cylinder reference lacks its persisted owner token")
    return {"persist_reference_sha256":sha256(data).hexdigest(),"persist_reference_bytes":len(data),"expected_corresponding_face_equality":int(Swapp.invoke(author.app,"IsSame",reference,expected)),"self_equality":int(Swapp.invoke(author.app,"IsSame",reference,reference)),"specific_equality_is_diagnostic":True}


def mate_state(author,model,assembly,child,components,rows,case):
    from AssemblyMateEvidence import mate_features
    features=list(mate_features(author,model))
    require(len(features)==1,"the source must have exactly one real concentric mate")
    feature=features[0]
    mate=author.typed(author.get(feature,"GetSpecificFeature2"),"Mate2")
    require(str(author.get(feature,"Name"))==case["mate_name"] and str(author.get(feature,"GetTypeName2"))=="MateConcentric" and int(author.get(mate,"Type"))==1 and int(author.get(mate,"GetMateEntityCount"))==2 and not author.get(feature,"IsSuppressed"),"the native concentric feature identity differs")
    require(author.get(feature,"GetFirstDisplayDimension") is None,"ordinary concentric mate unexpectedly owns a driving scalar")
    definition=author.typed(author.get(feature,"GetDefinition"),"ConcentricMateFeatureData")
    locked=bool(author.get(definition,"LockRotation"))
    alignment=int(author.get(mate,"Alignment"))
    require(locked==case["lock_rotation"] and alignment==case["api_alignment"],"the actual native alignment or rotation-lock option differs")
    local_face,_=local_cylinder(author,child,case)
    lookup={row["name"]:index for index,row in enumerate(rows)}
    endpoints=[]
    for ordinal in range(2):
        entity=author.typed(author.get(mate,"MateEntity",ordinal),"MateEntity2")
        component=author.typed(author.get(entity,"ReferenceComponent"),"Component2")
        name=str(author.get(component,"Name2"))
        require(name in lookup,"mate endpoint has an unexpected or repeated component")
        index=lookup.pop(name)
        require(int(author.get(component,"GetID"))==rows[index]["native_id"],"mate endpoint lost its actual occurrence ID")
        reference=author.get(entity,"Reference")
        require(reference is not None and int(author.get(entity,"ReferenceType2"))==2,"concentric endpoint is not its actual face selection")
        face=author.typed(reference,"Face2")
        require(bool(author.get(author.typed(author.get(face,"GetSurface"),"Surface"),"IsCylinder")),"mate reference does not resolve to a real cylindrical face")
        owner=author.get(author.typed(reference,"Entity"),"GetComponent")
        require(owner is not None and int(author.get(owner,"GetID"))==rows[index]["native_id"],"cylindrical reference belongs to another occurrence")
        values=[float(value) for value in author.get(entity,"EntityParams") or ()]
        require(len(values)==8 and all(map(isfinite,values)),"concentric entity parameters differ from their finite documented tuple")
        point,axis=values[:3],values[3:6]
        transform=rows[index]["transform"]
        expected_axis=transform[6:9]
        expected_point=world(transform,[*case["center_m"],0.0])
        require(isclose(norm(axis),1.0,abs_tol=1e-10) and norm(cross(axis,expected_axis))<1e-10 and norm(cross([point[j]-expected_point[j] for j in range(3)],expected_axis))<1e-10,"native mate cylinder axis differs from independently placed child")
        author.rec.close_number("native endpoint cylinder radius",values[6],case["radius_m"],absolute=1e-12)
        expected=author.get(components[index],"GetCorrespondingEntity",local_face)
        endpoints.append({"occurrence":name,"occurrence_native_id":rows[index]["native_id"],"selection_type":2,"surface_kind":"cylinder","point":point,"axis":axis,"radius_m":values[6],"reserved_radius2_observed":values[7],"observed_entity_parameter_count":len(values),"object_evidence":object_evidence(author,model,reference,expected)})
    parallel=norm(cross(endpoints[0]["axis"],endpoints[1]["axis"]))
    separation=norm(cross([endpoints[1]["point"][j]-endpoints[0]["point"][j] for j in range(3)],endpoints[0]["axis"]))
    require(parallel<1e-10 and separation<1e-10,"the actual native mate references are not coaxial")
    return {"name":case["mate_name"],"type":1,"native_feature_id":int(author.get(feature,"GetID")),"alignment":alignment,"rotation_locked":locked,"ordered_endpoints":endpoints,"axis_parallel_residual":parallel,"axis_distance_m":separation}


def capture(author,model,assembly,child_path,case,edited=False):
    import Swapp
    from AuthorAssemblySources import feature_tree,transform_matches
    objects=component_map(author,assembly,case,child_path)
    child=author.get(objects[0],"GetModelDoc2")
    require(child is not None and same_file(author.get(child,"GetPathName"),child_path),"the actual owned concentric child is unavailable")
    configuration(author,model,case["configuration"])
    configuration(author,child,case["configuration"])
    matrices=expected_transforms(case,edited)
    rows=[]
    for index,component in enumerate(objects):
        transform=[float(value) for value in author.get(author.typed(author.get(component,"Transform2"),"MathTransform"),"ArrayData")]
        require(transform_matches(transform,matrices[index]),"actual concentric occurrence differs from the independent pose")
        require(str(author.get(component,"ReferencedConfiguration"))==case["configuration"] and not author.get(component,"IsSuppressed") and not author.get(component,"IsHidden",False) and bool(author.get(component,"IsFixed"))==(index==0),"actual concentric component state differs")
        resolved=author.get(component,"GetModelDoc2")
        require(resolved is not None and same_file(author.get(resolved,"GetPathName"),child_path) and len(author.get(author.typed(resolved,"PartDoc"),"GetBodies2",0,True) or ())==1,"an occurrence lost the actual one-solid child")
        rows.append({"name":str(author.get(component,"Name2")),"native_id":int(author.get(component,"GetID")),"transform":transform,"configuration":case["configuration"],"fixed":index==0,"visible_child_bodies":1})
    require(len({row["native_id"] for row in rows})==2,"occurrence IDs are not distinct")
    predicted=geometry(case,edited)
    metrics={}
    for role,target in (("child",child),("assembly",model)):
        require(int(author.get(author.get(target,"Extension"),"GetWhatsWrongCount"))==0,"native concentric source has an error or warning")
        actual=author.rec.call("measure independent "+role+" cylinder geometry",Swapp.mass,target)
        require(isinstance(actual,dict) and "error" not in actual and actual.get("mass",0)>0,"native mass properties unavailable")
        for key in ("volume","area"): author.rec.close_number(role+" "+key,actual[key],predicted[role][key],absolute=1e-15)
        for index,(value,wanted) in enumerate(zip(actual["com"],predicted[role]["com"],strict=True)): author.rec.close_number(role+" centroid "+str(index),value,wanted,absolute=1e-12)
        metrics[role]=actual
    dimensions={}
    for name,wanted in zip(PARAMETERS,(case["radius_m"],case["edited_depth_m"] if edited else case["depth_m"]),strict=True):
        dimension=author.get(child,"Parameter",name)
        require(dimension is not None and int(author.get(dimension,"DrivenState"))==2 and not author.get(dimension,"ReadOnly"),"the actual source parameter is not independently editable")
        value=float(author.get(dimension,"SystemValue"))
        author.rec.close_number(name,value,wanted)
        dimensions[name]=value
    residual=coaxial_residual(case,[row["transform"] for row in rows])
    require(residual["parallel"]<1e-10 and residual["axis_distance_m"]<1e-10,"actual component geometry is not concentric")
    return {"occurrences":rows,"body_count":2,"mass":metrics,"dimensions_m":dimensions,"tree":feature_tree(author,model),"child_tree":feature_tree(author,child),"mate":mate_state(author,model,assembly,child,objects,rows,case)}


def signature(value):
    return {"tree":value["tree"],"child_tree":value["child_tree"],"body_count":value["body_count"],"occurrences":[{key:row[key] for key in ("name","native_id","configuration","fixed","visible_child_bodies")} for row in value["occurrences"]],"mate":{key:value["mate"][key] for key in ("name","type","native_feature_id","alignment","rotation_locked")}|{"ordered_endpoints":[{key:row[key] for key in ("occurrence","occurrence_native_id","selection_type","surface_kind")} for row in value["mate"]["ordered_endpoints"]]}}


def edit_live(author,model,assembly,child,child_path,case):
    import Swapp
    components=component_map(author,assembly,case,child_path)
    desired=expected_transforms(case,True)[1]
    transform=author.get(author.get(author.app,"GetMathUtility"),"CreateTransform",Swapp.VARIANT(Swapp.pythoncom.VT_ARRAY|Swapp.pythoncom.VT_R8,desired))
    require(transform is not None and bool(author.get(components[1],"SetTransformAndSolve2",transform)),"the valid axial or unlocked spin edit was rejected")
    dimension=author.get(child,"Parameter",PARAMETERS[1])
    require(dimension is not None and int(author.get(dimension,"SetSystemValue3",case["edited_depth_m"],1,Swapp.nothing()))==0,"native child depth edit was rejected")
    require(bool(author.get(child,"ForceRebuild3",False)) and bool(author.get(model,"ForceRebuild3",False)),"the edited concentric pair did not rebuild")
