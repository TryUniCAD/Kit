from dataclasses import replace
from pathlib import PureWindowsPath

from PerpendicularMath import prediction, rotation


def cases():
    common = [['x',11.9],['y',-23.7],['z',37.1]]
    return [
        {'id':'G01','name':'NeutralPerpPair','child_name':'NeutralPerpPrism','size_m':[.04321,.01873,.01037],
         'edit_depth_m':.01591,'edit_rotation_deg':-27.9,'fixed_occurrence':0,
         'placements':[{'orientation':common,'translation_m':[.00413,-.00829,.00641]}, {'orientation':common,'translation_m':[.14937,.02341,-.01723]}],
         'endpoints':[{'occurrence':0,'axis':'x'},{'occurrence':1,'axis':'y'}]},
        {'id':'G02','name':'NeutralPerpQuarter','child_name':'NeutralQuarterPrism','size_m':[.03517,.02243,.00731],
         'edit_depth_m':.01319,'edit_rotation_deg':34.7,'fixed_occurrence':0,
         'placements':[{'orientation':common,'translation_m':[-.01131,.01907,.00419]}, {'orientation':[['y',90.],*common],'translation_m':[.16319,-.02117,.02931]}],
         'endpoints':[{'occurrence':0,'axis':'z'},{'occurrence':1,'axis':'z'}]},
        {'id':'G03','name':'NeutralPerpReverse','child_name':'NeutralReversePrism','size_m':[.04713,.01739,.00917],
         'edit_depth_m':.01643,'edit_rotation_deg':-41.3,'fixed_occurrence':1,
         'placements':[{'orientation':common,'translation_m':[.01319,.00571,-.00217]}, {'orientation':common,'translation_m':[.17213,-.02873,.01357]}],
         'endpoints':[{'occurrence':1,'axis':'y'},{'occurrence':0,'axis':'x'}]},
        {'id':'G04','name':'NeutralPerpIdentity','child_name':'NeutralIdentityPrism','size_m':[.03971,.02513,.01147],
         'edit_depth_m':.01829,'edit_rotation_deg':19.3,'fixed_occurrence':1,
         'placements':[{'orientation':[],'translation_m':[.00173,-.00319,.00611]}, {'orientation':[],'translation_m':[.15431,.01937,-.02413]}],
         'endpoints':[{'occurrence':0,'axis':'z'},{'occurrence':1,'axis':'y'}]},
    ]


def document(spec):
    from interchange.Enums.EnumValues import ParameterRole, ValueKind
    from interchange.Records.RecordParameter import Parameter, ParameterValue
    from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation
    from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import MakePlainDoc

    width, height, depth = [value * 1000 for value in spec['size_m']]
    result = MakePlainDoc(spec['child_name'], width, height, depth)
    sketch = result.sketches[0]
    lengths = [Parameter('parameter/'+key, 'D'+str(i+1), ParameterValue(value, ValueKind.KLength,'mm'),
                         ParameterRole.KDriving, owner_id=sketch.id) for i,(key,value) in enumerate((('width',width),('height',height)))]
    rules = [SketchRelation('relation/axis/'+str(i), 'horizontal' if i%2==0 else 'vertical', (ConstraintRef(value.id),)) for i,value in enumerate(sketch.entities)]
    rules += [SketchRelation('relation/length/'+str(i),'distance',(ConstraintRef(sketch.entities[i].id,'start'),ConstraintRef(sketch.entities[i].id,'end')),param.id) for i,param in enumerate(lengths)]
    sketch = replace(sketch,constraints=tuple(rules),parameter_ids=tuple(p.id for p in lengths))
    return replace(result, sketches=(sketch,),parameters=(lengths[1],result.parameters[0],lengths[0]),
                   configurations=(replace(result.configurations[0],name='Default'),))


def request(spec, native_root):
    from interchange.serialization.EncodeData import ToData
    from tests.Convert.Solidworks.Research.Construction.Assembly.MakeAsmInput import MakeAsmInput
    from tests.Convert.Solidworks.Research.Construction.Part.BlindCaseInput import BlindCaseInput

    child = BlindCaseInput(spec['child_name'],False)
    child['document'] = ToData(document(spec))
    child['settings']['output']['path_name'] = str(PureWindowsPath(native_root)/(spec['child_name']+'.SLDPRT'))
    width,height,_ = spec['size_m']
    child['rectangle_dimensions'] = {'width_text_m':[-width*.15,-height/2-.0067], 'height_text_m':[width/2+.0082,height*.11], 'route_centerline':False}
    assembly = MakeAsmInput(spec['name'],False)['assembly']
    assembly['output']['path_name'] = str(PureWindowsPath(native_root)/(spec['name']+'.SLDASM'))
    occurrences = []
    for i,placement in enumerate(spec['placements']):
        matrix = rotation(placement['orientation'])
        occurrences.append({'name':spec['child_name']+'-'+str(i+1),'origin':placement['translation_m'],'u':matrix[:3],'v':matrix[3:6]})
    return {'assembly':assembly,'child':child,'occurrences':occurrences,
            'mates':[{'kind':'perpendicular','name':'Perpendicular1','endpoints':spec['endpoints']}], 'fixed_occurrence':spec['fixed_occurrence']}


def prediction_pair(spec):
    return {'source':prediction(spec), 'edited':prediction(spec,True)}
