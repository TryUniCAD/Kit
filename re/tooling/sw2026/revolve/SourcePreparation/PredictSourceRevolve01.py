from math import cos,sin,tau,isclose


def predict(geometry,angle=None):
    theta=geometry['positive_angle_rad'] if angle is None else angle
    if not 0<theta<=tau:raise ValueError('positive ordinary angle exceeds the defined sweep')
    vertices=geometry['contour_points_mm'];axis=geometry['axis_start_mm'][0]*.001
    inner=min(point[0]*.001 for point in vertices)-axis
    outer=max(point[0]*.001 for point in vertices)-axis
    low=min(point[1]*.001 for point in vertices);high=max(point[1]*.001 for point in vertices)
    if not 0<inner<outer or not low<high:raise ValueError('source rectangular sweep is not independently defined')
    height=high-low;difference=outer*outer-inner*inner
    volume=theta*difference*height*.5
    area=theta*((outer+inner)*height+difference)
    if not isclose(theta,tau,rel_tol=0,abs_tol=1e-12):area+=2*(outer-inner)*height
    distance=2*(outer**3-inner**3)/(3*difference*theta)
    sense=1 if geometry['reverse'] else -1
    return {'volume_m3':volume,'area_m2':area,'com_m':[axis+distance*sin(theta),(low+high)*.5,sense*distance*(1-cos(theta))]}


def compare(geometry,states):
    records=[]
    for name,state in states.items():
        measured=state['mass'];value=predict(geometry,state['angle_radians']);count=0
        for actual,expected in [(measured['volume'],value['volume_m3']),(measured['area'],value['area_m2']),*zip(measured['com'],value['com_m'],strict=True)]:
            if not isclose(actual,expected,rel_tol=1e-10,abs_tol=1e-14):raise ValueError('independent source sweep metric differs from recorded native state '+name)
            count+=1
        if state['reverse']!=geometry['reverse']:raise ValueError('native reverse state differs from the actual source owner')
        records.append({'state':name,'numeric_checks':count,'expected':value,'recorded_native':measured,'passed':True})
    return records
