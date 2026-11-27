import hashlib
import json
from pathlib import Path
import sys

from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, ResolveField, SameNodes
from convert.adapters.Fusion.Native.Graph.GraphValues import TextValue
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Parameters.ReadParameters import CheckBinding, ProjectParam, ReadParameters
from convert.adapters.Fusion.Native.Policy.CheckGraph import CheckGraph
from convert.adapters.Fusion.Native.Policy.CheckScopes import CheckScopes
from convert.adapters.Fusion.Native.Policy.CheckAuxiliary import CheckSceneRefs
from convert.adapters.Fusion.Native.Projection.ReadMaterial import ReadMaterial
from convert.adapters.Fusion.Native.Rectangle.CheckRegion import CheckRegion
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases

root=Path(sys.argv[1]).resolve(); output=Path(sys.argv[2]).resolve(); output.mkdir(exist_ok=False)
rows=[]
for case in ReadDualCases():
    data=case.Source.read_bytes(); assert hashlib.sha256(data).hexdigest()==case.Digest
    model=ReadDocument(data);graph=BuildGraph(model);context=SelectExtrusion(graph)
    row=dict(source=str(case.Source.relative_to(root)),sha256=case.Digest,steps={})
    shape=ReadCircle(graph,context)
    for name,program in [('graph',lambda:CheckGraph(graph,context)),('scope',lambda:CheckScopes(graph,context,model.Asset.AssetId)),('region',lambda:CheckRegion(graph,context,(shape.CurveNode,),model.Asset.AssetId)),('scene',lambda:CheckSceneRefs(graph,model.Graphics)),('material',lambda:ReadMaterial(graph,context,model)),('original_parameters',lambda:ReadParameters(graph,context,AllowTaper=True))]:
        try:
            result=program();row['steps'][name]=dict(passed=True)
            if name=='material':row['material']=dict(identity=result.id,density=result.Density)
        except Exception as error:row['steps'][name]=dict(passed=False,reason=type(error).__name__+': '+str(error))
    try:
        table=ResolveField(graph,context.Component,'rParameterTable','ParameterTable');nodes=LinkedNodes(graph,table,'children');SameNodes(nodes,graph.ByClass('Parameter'))
        catalog={TextValue(n.Fields['userName']):n for n in nodes};assert len(catalog)==len(nodes) and '' not in catalog
        bindings=tuple(ResolveField(graph,context.Extrude,key,'DcDoubleParameter') for key in ('rAlongDistance','rAgainstDistance','rTaperAngle','side2TaperAngle'))
        SameNodes(bindings,graph.ByClass('DcDoubleParameter'))
        identifiers=tuple(IntegerValue(n.Fields['rparamId']) for n in bindings);assert len(set(identifiers))==4 and min(identifiers)>0 and max(identifiers)<=IntegerValue(context.Fragment.Fields['nextParamId'])
        parameters=tuple(CheckBinding(graph,b,context) for b in bindings);assert len({n.Identity for n in parameters})==4
        for parameter,role,expected,unit in zip(parameters,('AlongDistance','AgainstDistance','TaperAngle','Side2TaperAngle'),(case.FirstMm/10,case.SecondMm/10,case.FirstTaper,case.SecondTaper),('mm','mm','deg','deg'),strict=True):
            assert parameter.Fields['name']==role and parameter.Fields['unit']==unit
            assert abs(parameter.Fields['value']-expected)<=1e-10
        owners={n.Identity:context.Extrude for n in parameters}
        projected=tuple(ProjectParam(n,catalog,owners.get(n.Identity)) for n in nodes)
        row['parameters']=[dict(identity=p.id,name=p.name,owner=p.owner_id,value=p.value.value,unit=p.value.unit,expression=p.expression.source if p.expression else None) for p in projected]
        row['steps']['independent_parameters']=dict(passed=True)
    except Exception as error:row['steps']['independent_parameters']=dict(passed=False,reason=type(error).__name__+': '+str(error))
    rows.append(row)
summary={name:sum(row['steps'][name]['passed'] for row in rows) for name in rows[0]['steps']}
(output/'Receipt.json').write_text(json.dumps(dict(base='9c5ff325bdd9de89074821bcf7181f4056f20d8e',models=False,native_calls=0,rows=rows,summary=summary),indent=2)+'\n')
print(json.dumps(summary))
