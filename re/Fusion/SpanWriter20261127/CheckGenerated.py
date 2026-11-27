from pathlib import Path
import hashlib
import json
import math
import sys

from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Graph.ReadExtentMode import ReadExtentMode
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields, PointCoords
from convert.adapters.Fusion.Native.Circular.RotaryMass import RotaryMass
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.adapters.Fusion.Native.Parameters.ReadParameters import ReadParameters

root=Path(sys.argv[1]);checks=[]
records=json.loads((root/'Results.json').read_text())
for case in records['cases'] if isinstance(records,dict) else records:
    radius,first,second,offset=case['values_mm']
    path=root/(case['case']+'.f3d');raw=path.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==case['sha256']
    model=ReadDocument(raw);graph=BuildGraph(model);context=SelectExtrusion(graph)
    params=ReadParameters(graph,context)
    byrole={p.attributes['native_name']:p for p in params if p.owner_id==context.Extrude.Identity}
    assert len(params)==6 and len(byrole)==5
    assert ReadExtentMode(context.Extrude)=='two_sided'
    for role,wanted in [('AlongDistance',first),('AgainstDistance',second),('ProfileOffset',offset),('TaperAngle',0),('Side2TaperAngle',0)]:
        actual=byrole[role].value.value
        checks.append(dict(case=case['case'],field=role,expected=wanted,actual=actual,passed=math.isclose(actual,wanted,abs_tol=1e-10)))
    for field,role in [('rAlongDistance','AlongDistance'),('rAgainstDistance','AgainstDistance'),('profileOffset','ProfileOffset'),('rTaperAngle','TaperAngle'),('side2TaperAngle','Side2TaperAngle')]:
        binding=graph.Resolve(context.Extrude.Fields[field]);parameter=graph.Resolve(binding.Fields['parameter'])
        assert parameter.Identity==byrole[role].id and graph.Resolve(parameter.Fields['dcParameter'])==binding
    assert context.Extrude.Fields['profileLocaltionType']==1
    assert context.Extrude.Fields['booleanOperation']==4
    cache=ObjectFields(context.BodyNode.Fields['cache'])
    RotaryMass(context,FrustumBody(radius,radius,first+second,(0.,0.,offset-second)))
    r=radius/10;h=(first+second)/10;center=(2*offset+first-second)/20
    for field,wanted in [('volume',math.pi*r*r*h),('area',2*math.pi*r*(r+h))]:
        checks.append(dict(case=case['case'],field=field,expected=wanted,actual=cache[field],passed=math.isclose(cache[field],wanted,rel_tol=1e-12)))
    assert all(math.isclose(actual,wanted,abs_tol=1e-10) for actual,wanted in zip(PointCoords(cache['cog']),(0.,0.,center)))
    try:
        from convert import open_document
        open_document(path)
        boundary=False;reason='unexpected strict read'
    except ValueError as error:boundary=True;reason=str(error)
    checks.append(dict(case=case['case'],field='strict_boundary',passed=boundary,reason=reason))
report=dict(reader_revision='7ce58d3962f89c5c184e1fd993126e4927f9d73d',models=False,native_acceptance='not_run_transport_unavailable',passed=sum(row['passed'] for row in checks),failed=sum(not row['passed'] for row in checks),checks=checks)
(root/'Comparison.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='checks'}));assert report['failed']==0
