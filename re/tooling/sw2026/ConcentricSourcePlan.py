from __future__ import annotations

import math
import os
import secrets

from AuthorCurves import require

SCHEMA="kit.sw2026.concentric-native-source-spec.v1"
SLOTS=("D01","D02","D03","H01","H02")
PARAMETERS=("D1@CurveSketch","D1@CurveBoss")


def dot(a,b):
    return sum(x*y for x,y in zip(a,b,strict=True))


def cross(a,b):
    return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]


def norm(value):
    return math.sqrt(dot(value,value))


def mul(a,b):
    return [sum(a[row*3+k]*b[k*3+col] for k in range(3)) for row in range(3) for col in range(3)]


def rotation(axis,angle):
    values=[0.0]*9
    index="xyz".index(axis)
    first,second=(index+1)%3,(index+2)%3
    values[index*3+index]=1.0
    values[first*3+first]=values[second*3+second]=math.cos(angle)
    values[first*3+second]=math.sin(angle)
    values[second*3+first]=-math.sin(angle)
    return values


def vector(matrix,point):
    return [sum(point[row]*matrix[row*3+col] for row in range(3)) for col in range(3)]


def world(matrix,point):
    result=vector(matrix,point)
    return [result[index]+matrix[9+index] for index in range(3)]


def expected_transforms(case,edited=False):
    common=rotation("z",0.0)
    for axis,angle in zip("xyz",case["common_euler_rad"],strict=True):
        common=mul(common,rotation(axis,angle))
    spin=case["spin_rad"]+(case["spin_edit_rad"] if edited and not case["lock_rotation"] else 0.0)
    moving=mul(rotation("z",spin),common)
    if case["api_alignment"]==1:
        moving=mul(rotation("x",math.pi),moving)
    center=[*case["center_m"],0.0]
    fixed=[*common,*case["anchor_translation_m"],1.0,0.0,0.0,0.0]
    origin=world(fixed,center)
    normal=common[6:9]
    distance=case["separation_m"]+(case["slide_edit_m"] if edited else 0.0)
    location=[origin[index]+distance*normal[index] for index in range(3)]
    relative=vector(moving,center)
    translation=[location[index]-relative[index] for index in range(3)]
    return [fixed,[*moving,*translation,1.0,0.0,0.0,0.0]]


def coaxial_residual(case,matrices):
    center=[*case["center_m"],0.0]
    points=[world(value,center) for value in matrices]
    normals=[value[6:9] for value in matrices]
    difference=[points[1][index]-points[0][index] for index in range(3)]
    return {"parallel":norm(cross(*normals)),"axis_distance_m":norm(cross(difference,normals[0])),"normal_dot":dot(*normals)}


def geometry(case,edited=False):
    radius=case["radius_m"]
    depth=case["edited_depth_m"] if edited else case["depth_m"]
    local=[*case["center_m"],depth/2]
    centers=[world(matrix,local) for matrix in expected_transforms(case,edited)]
    volume=math.pi*radius*radius*depth
    area=2*math.pi*radius*(radius+depth)
    return {"child":{"volume":volume,"area":area,"com":local},"assembly":{"volume":2*volume,"area":2*area,"com":[sum(value[index] for value in centers)/2 for index in range(3)]},"body_count":2}


def child_case(case):
    return {"id":case["id"]+"Child","name":case["child_name"],"plane":"front","profile":{"kind":"circle","center_mm":[value*1000 for value in case["center_m"]],"radius_mm":case["radius_m"]*1000},"depth_mm":case["depth_m"]*1000,"end_condition":"blind","reverse":False,"expected_bodies":1,"dimension_kind":"radial","edit":{"target":"depth","factor":case["edited_depth_m"]/case["depth_m"]}}


def validate(case):
    keys={"id","name","child_name","configuration","radius_m","depth_m","edited_depth_m","center_m","common_euler_rad","anchor_translation_m","separation_m","spin_rad","slide_edit_m","spin_edit_rad","api_alignment","lock_rotation","endpoint_order","mate_name"}
    require(type(case) is dict and set(case)==keys,"concentric source has undeclared intent")
    require(case["id"] in SLOTS and case["configuration"]=="Default" and case["mate_name"]=="Concentric1","unsupported source identity or configuration")
    for key in ("name","child_name"):
        require(type(case[key]) is str and case[key] and all(value not in case[key] for value in ('/','\\',':','\0')),"source names must be explicit ordinary basenames")
    for key,size in (("center_m",2),("common_euler_rad",3),("anchor_translation_m",3)):
        require(type(case[key]) in (list,tuple) and len(case[key])==size and all(type(value) in (int,float) and math.isfinite(value) for value in case[key]),"invalid source geometry or pose")
    for key in ("radius_m","depth_m","edited_depth_m","separation_m","spin_rad","slide_edit_m","spin_edit_rad"):
        require(type(case[key]) in (int,float) and math.isfinite(case[key]),"source scalar must be finite")
    require(min(case["radius_m"],case["depth_m"],case["edited_depth_m"])>1e-6 and case["depth_m"]!=case["edited_depth_m"],"source dimensions and actual edit must be positive")
    require(case["separation_m"]>4*max(case["depth_m"],case["edited_depth_m"]) and case["slide_edit_m"]>0,"source cylinders must stay spatially separated")
    require(type(case["lock_rotation"]) is bool and type(case["api_alignment"]) is int and case["api_alignment"] in (0,1) and type(case["endpoint_order"]) is list and all(type(value) is int for value in case["endpoint_order"]) and sorted(case["endpoint_order"])==[0,1],"unsupported concentric alignment lock or participant order")
    for edited in (False,True):
        values=coaxial_residual(case,expected_transforms(case,edited))
        require(values["parallel"]<1e-12 and values["axis_distance_m"]<1e-12,"independent source placement is not coaxial")
        require(math.isclose(values["normal_dot"],1 if case["api_alignment"]==0 else -1,abs_tol=1e-12),"independent source alignment differs")
    return case


def disclosed_cases():
    common={"configuration":"Default","mate_name":"Concentric1","slide_edit_m":0.01237,"spin_edit_rad":0.2917}
    rows=[
        {"id":"D01","name":"ConcentricD01AlignedFree","child_name":"ConcentricD01Child","radius_m":0.00719,"depth_m":0.03137,"edited_depth_m":0.04691,"center_m":[0.00263,-0.00417],"common_euler_rad":[0.0,0.0,0.0],"anchor_translation_m":[0.0413,-0.0271,0.0187],"separation_m":0.2371,"spin_rad":0.3719,"api_alignment":0,"lock_rotation":False,"endpoint_order":[0,1]},
        {"id":"D02","name":"ConcentricD02AlignedLocked","child_name":"ConcentricD02Child","radius_m":0.00719,"depth_m":0.03137,"edited_depth_m":0.04691,"center_m":[0.00263,-0.00417],"common_euler_rad":[0.0,0.0,0.0],"anchor_translation_m":[0.0413,-0.0271,0.0187],"separation_m":0.2371,"spin_rad":0.3719,"api_alignment":0,"lock_rotation":True,"endpoint_order":[0,1]},
        {"id":"D03","name":"ConcentricD03AntiFree","child_name":"ConcentricD03Child","radius_m":0.00583,"depth_m":0.02473,"edited_depth_m":0.03617,"center_m":[0.00439,0.00197],"common_euler_rad":[-0.2719,0.3917,-0.4783],"anchor_translation_m":[0.0671,-0.0349,0.0217],"separation_m":0.1931,"spin_rad":0.6913,"api_alignment":1,"lock_rotation":False,"endpoint_order":[1,0]},
    ]
    return [validate(dict(common,**row)) for row in rows]


def heldout_cases():
    require(os.name=="nt","unseen source designs are created only inside the guest")
    rng=secrets.SystemRandom()
    result=[]
    for identifier in ("H01","H02"):
        depth=rng.randint(1800,3900)/100000
        edited=depth*1.317+0.001019
        result.append(validate({"id":identifier,"name":"Concentric"+identifier,"child_name":"Concentric"+identifier+"Child","configuration":"Default","mate_name":"Concentric1","radius_m":rng.randint(470,1280)/100000,"depth_m":depth,"edited_depth_m":edited,"center_m":[rng.randint(-630,630)/100000,rng.randint(-630,630)/100000],"common_euler_rad":[rng.uniform(-0.73,0.73) for _ in range(3)],"anchor_translation_m":[rng.randint(-9700,9700)/100000 for _ in range(3)],"separation_m":6*max(depth,edited)+0.01937,"spin_rad":rng.uniform(-0.91,0.91),"slide_edit_m":rng.randint(917,2317)/100000,"spin_edit_rad":rng.uniform(0.19,0.47),"api_alignment":0 if identifier=="H01" else 1,"lock_rotation":identifier=="H02","endpoint_order":[0,1] if identifier=="H01" else [1,0]}))
    return result
