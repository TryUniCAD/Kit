from pathlib import Path
from hashlib import sha256
from math import isclose
import argparse,json,sys


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise ValueError('choose an unused output')
    sys.path.insert(0,str(args.root/'src'))
    from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
    from interchange.geometry.Models.GeometryCurves import LineGeometry
    from interchange.geometry.Models.Transform import Transform
    from interchange.geometry.Models.VectorPlane import PlaneVector
    from interchange.geometry.Models.VectorSpace import SpaceVector
    cases=[{'width':17.125,'height':9.75,'depth':4.625,'xy':[-2.25,5.5],'origin':[4.,-7.,2.],'u':[1.,0.,0.],'v':[0.,1.,0.],'n':[0.,0.,1.]},
           {'width':30.25,'height':13.875,'depth':8.625,'xy':[3.125,-4.375],'origin':[-6.,3.,5.],'u':[0.,1.,0.],'v':[-1.,0.,0.],'n':[0.,0.,1.]},
           {'width':31.75,'height':18.625,'depth':12.375,'xy':[-5.125,-3.875],'origin':[7.,2.,-4.],'u':[0.,0.,-1.],'v':[0.,1.,0.],'n':[1.,0.,0.]}]
    rows=[]
    for index,case in enumerate(cases):
        x,y=case['xy'];w,h,d=case['width'],case['height'],case['depth']
        points=[(x,y),(x+w,y),(x+w,y+h),(x,y+h)]
        curves=tuple(LineGeometry(PlaneVector(*a),PlaneVector(*b)) for a,b in zip(points,points[1:]+points[:1]))
        frame=Transform(SpaceVector(*case['origin']),SpaceVector(*case['u']),SpaceVector(*case['v']),SpaceVector(*case['n']))
        bodyid='analytic-control:'+str(index)
        model,volume,area,_=BuildPrism(bodyid,frame,curves,0.,d)
        expected=[tuple(case['origin'][j]+px*case['u'][j]+py*case['v'][j]+pz*case['n'][j] for j in range(3)) for pz in (0.,d) for px,py in points]
        actual=[tuple(getattr(vertex.point,k) for k in ('x','y','z')) for vertex in model.vertices]
        if actual!=expected or model.validate(frozenset({bodyid})) or (len(model.vertices),len(model.edges),len(model.faces),len(model.bodies))!=(8,12,6,1):raise ValueError('generated SDK prism topology differs from independent corners')
        if not isclose(volume,w*h*d,rel_tol=1e-14) or not isclose(area,2*(w*h+w*d+h*d),rel_tol=1e-14):raise ValueError('generated SDK prism measures differ')
        rows.append({'input':case,'vertices_match_independent_math':True,'topology_errors':[],'volume_mm3':volume,'area_mm2':area,'edge_count':12,'native_kernel_identity':False})
    report={'passed':True,'cases':rows,'models_generated':len(rows),'native_files_generated':0,'native_runs':0,'still_sealed_inputs_read':0,'source_native_files_read':0}
    args.output.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps({'passed':True,'sha256':sha256(args.output.read_bytes()).hexdigest()}))


if __name__=='__main__':main()
