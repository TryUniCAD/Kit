import argparse
from collections.abc import Mapping
from dataclasses import fields, is_dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def plain(value):
    if is_dataclass(value):
        return {field.name: plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    return value


def differences(first, second):
    result = []
    def visit(left, right, path):
        if left == right:
            return
        if isinstance(left, dict) and isinstance(right, dict) and left.keys() == right.keys():
            for key in left:
                visit(left[key], right[key], path + '/' + key)
        elif isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
            for index, (a, b) in enumerate(zip(left, right, strict=True)):
                visit(a, b, path + '/' + str(index))
        else:
            result.append({'path': path, 'qualified_fixture': left, 'existing_public_projection': right})
    visit(plain(first), plain(second), '')
    return result


def portable(request, prediction):
    from MakeAssemblyBoundaryCase import make_case, principal
    from interchange.assembly.AssemblyEnums import MateAlignment, MateEntityKind, MateKind
    from interchange.assembly.MateConstraint import MateConstraint
    from interchange.assembly.MateEntity import MateEntity
    from interchange.assembly.TransformMatrix import TransformMatrix
    from interchange.serialization.Deserialize import FromData

    template = make_case(2)
    graph = template.assembly
    child = FromData(request['child']['document'])
    planes = principal('child')
    child = replace(child, support_planes=planes, sketches=(replace(child.sketches[0], support_plane_id=planes[2].id),))
    configuration, = child.configurations
    root_config = replace(template.configurations[0], name=request['assembly']['configuration_name'])
    root, definition = graph.definitions
    definitions = (replace(root, name=request['assembly']['name'], configuration_name=root_config.name),
                   replace(definition, name=child.metadata['name'], configuration_name=configuration.name,
                           configuration_id=configuration.id, body_ids=tuple(row.id for row in child.bodies)))
    instances = []
    for index, (item, matrix) in enumerate(zip(graph.instances, prediction['source']['native_transforms'], strict=True)):
        columns = (matrix[0],matrix[3],matrix[6],matrix[9]*1000,
                   matrix[1],matrix[4],matrix[7],matrix[10]*1000,
                   matrix[2],matrix[5],matrix[8],matrix[11]*1000,0.,0.,0.,1.)
        instances.append(replace(item, name=request['occurrences'][index]['name'], transform=TransformMatrix(columns),
                                 configuration_name=configuration.name, configuration_id=configuration.id,
                                 fixed=index==request['fixed_occurrence']))
    rule = request['mates'][0]
    ends = tuple(MateEntity('perpendicular/entity/'+str(index),root.id,(instances[row['occurrence']].id,),MateEntityKind.PLANE,
                            source_entity_id='child/plane/'+row['axis']) for index,row in enumerate(rule['endpoints']))
    mate = MateConstraint('mate/perpendicular',rule['name'],MateKind.PERPENDICULAR,root.id,tuple(row.id for row in ends),alignment=MateAlignment.KUnknown)
    graph = replace(graph,definitions=definitions,instances=tuple(instances),documents=(replace(graph.documents[0],document=child),),
                    mate_entities=ends,mates=(mate,),mate_groups=(replace(graph.mate_groups[0],mate_ids=(mate.id,)),))
    result=replace(template,configurations=(root_config,),parameters=(),assembly=graph,metadata={'name':request['assembly']['name']})
    result.assert_valid()
    return result


def main():
    parser=argparse.ArgumentParser()
    for key in ('root','request','prediction','output'):parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args()
    root=args.root.resolve(strict=True)
    sys.path[:0]=[str(root/'src'),str(root),str(root/'re/tooling/sw2026')]
    from convert import write_document
    from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.MakePlanarGroup import MakePlanarGroup
    from convert.adapters.solidworks.Archive.Construction.Part.MakeRectDimPart import MakeRectDimPart
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import ProjectRectDims
    from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import RectDimInput
    from convert.adapters.solidworks.Core.AssemblyPreparation.Children.MakeChildRecipe import MakeChildRecipe
    from convert.adapters.solidworks.Core.AssemblyPreparation.Children.ReadAsmPlanes import ReadAsmPlanes
    from convert.adapters.solidworks.Core.AssemblyPreparation.Children.ReadRectDisplay import ReadRectDisplay
    from convert.adapters.solidworks.Core.AssemblyPreparation.Mates.CheckAsmMate import CheckAsmMate
    from convert.adapters.solidworks.Core.AssemblyPreparation.Mates.ReadAsmRules import ReadAsmRules
    from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
    from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.ReadAsmPaths import ReadAsmPaths
    from convert.adapters.solidworks.Core.AssemblyPreparation.Placements.ReadAsmPlace import ReadAsmPlace
    from convert.adapters.solidworks.Core.AssemblyPreparation.Recipe.MakeAsmRecipe import MakeAsmRecipe
    from SdkAssemblySettings import assembly_settings, occurrence_settings
    from SdkBlindPartSettings import settings
    from SdkPlanarGroupSettings import group_settings

    request=json.loads(args.request.read_bytes());prediction=json.loads(args.prediction.read_bytes())
    document=portable(request,prediction)
    model=ReadAsmModel(document)
    root_planes=ReadAsmPlanes(document);child_planes=ReadAsmPlanes(model.ChildDocument)
    child_doc=replace(model.ChildDocument,support_planes=(child_planes['z'],))
    epoch=request['assembly']['output']['saved_at']
    paths=ReadAsmPaths(model.RootValue.name,model.ChildValue.name,request['assembly']['output']['path_name'],epoch)
    plan=ProjectRectDims(child_doc)
    actual_child=MakeChildRecipe(child_doc,plan,child_planes,paths.ChildValue)
    actual_root=MakeAsmRecipe(model,actual_child,root_planes,paths.ParentValue)
    actual_dims=ReadRectDisplay(plan,actual_child)
    actual_occurrences=tuple(ReadAsmPlace(value) for value in model.Occurrences)
    expected_child=settings(request['child']['settings']);expected_root=assembly_settings(request['assembly'])
    raw_dims=request['child']['rectangle_dimensions']
    expected_dims=RectDimInput(tuple(raw_dims['width_text_m']),tuple(raw_dims['height_text_m']),expected_child.DesignIntent,expected_child.SelectedLeader,raw_dims['route_centerline'])
    expected_occurrences=occurrence_settings(request['occurrences']);mates=group_settings(request['mates'])
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    gates={}
    for name,operation in [('ReadAsmRules',lambda:ReadAsmRules(document,model,child_planes)),('CheckAsmMate',lambda:CheckAsmMate(model.GraphValue.mates[0],model.RootValue.id))]:
        try:operation()
        except (ValueError,TypeError) as error:gates[name]={'rejected':True,'error':str(error)}
        else:raise ValueError('the current public mate gate unexpectedly admitted perpendicular')
    for name,format_id in [('default',None),('explicit','solidworks.sldasm')]:
        folder=output/name;folder.mkdir()
        target=folder/(model.RootValue.name+'.SLDASM')
        try:write_document(document,target,destination_format=format_id,allow_carrier=False,values={'native_destination':request['assembly']['output']['path_name']})
        except Exception as error:
            require(not list(folder.iterdir()),'the public rejection published a partial bundle')
            gates[name]={'rejected_before_output':True,'error':str(error)}
        else:raise ValueError('the current registry unexpectedly enabled perpendicular output')
    summaries={}
    candidates={}
    for label,child_input,root_input,dimensions,occurrences in [('qualified',expected_child,expected_root,expected_dims,expected_occurrences),
                                                            ('public-projection',actual_child,actual_root,actual_dims,actual_occurrences)]:
        child=MakeRectDimPart(child_doc,child_input,dimensions)
        parent=MakePlanarGroup(child,root_input,occurrences,mates,model.FixedIndex)
        candidates[label]={'parent':parent,'child':child}
        folder=output/label;folder.mkdir()
        for role,value in candidates[label].items():(folder/((model.RootValue.name if role=='parent' else model.ChildValue.name)+('.SLDASM' if role=='parent' else '.SLDPRT'))).write_bytes(value.BytesValue)
        summaries[label]={role:{'bytes':len(value.BytesValue),'sha256':sha256(value.BytesValue).hexdigest(),
                               'streams':{name:{'bytes':len(data),'sha256':sha256(data).hexdigest()} for name,data in value.StreamsValue.items()}}
                          for role,value in candidates[label].items()}
    changed={role:[name for name in candidates['qualified'][role].StreamsValue
                   if candidates['qualified'][role].StreamsValue[name]!=candidates['public-projection'][role].StreamsValue.get(name)] for role in ('parent','child')}
    receipt={'schema':'kit.sw2026.perpendicular-public-projection-disclosed-audit.v1','registry_enabled':False,'native_acceptance':False,
             'actual_guards':gates,'child_recipe_differences':differences(expected_child,actual_child),'root_recipe_differences':differences(expected_root,actual_root),
             'dimension_placement_differences':differences(expected_dims,actual_dims),'occurrence_projection_differences':differences(expected_occurrences,actual_occurrences),
             'ordered_geometry':plain(plan.VerticesValue),'bundles':summaries,'changed_streams':changed,'projection_candidate_is_not_public_admission':True,
             'native_processes_started':0,'heldout_payloads_read':0,'source_root':str(root)}
    data=(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+'\n').encode();(output/'ProjectionAudit.json').write_bytes(data)
    print(json.dumps({'receipt_sha256':sha256(data).hexdigest(),'child_recipe_differences':len(receipt['child_recipe_differences']),
                      'root_recipe_differences':len(receipt['root_recipe_differences']),'dimension_placement_differences':len(receipt['dimension_placement_differences']),
                      'occurrence_projection_differences':len(receipt['occurrence_projection_differences']),'changed_streams':changed,
                      'registry_enabled':False,'native_processes_started':0,'heldout_payloads_read':0},sort_keys=True))


if __name__=='__main__':main()
