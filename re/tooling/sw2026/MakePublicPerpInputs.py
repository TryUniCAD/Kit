import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import sys


def write(path,value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')
    return sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    for key in ('root','fixtures','output'):parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args();root=args.root.resolve(strict=True)
    sys.path[:0]=[str(Path(__file__).resolve().parent),str(root/'src'),str(root),str(root/'re/tooling/sw2026')]
    from ProbePerpendicularPublic import portable
    from interchange.Records.RecordParameter import Parameter,ParameterValue
    from interchange.Enums.EnumValues import ValueKind
    from interchange.serialization.EncodeData import ToData
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    docs={};records=[]
    for case in ('G01','G04'):
        folder=args.fixtures/case
        request=json.loads((folder/'Request.json').read_bytes());prediction=json.loads((folder/'Prediction.json').read_bytes())
        doc=portable(request,prediction);docs[case]=doc
        native=PureWindowsPath(r'\\Mac\Home\Documents\UniCAD\Oracle121Takeover\PublicPerpendicularRegistry01\GeneratedInput')/(doc.metadata['name']+'.SLDASM')
        data={'document':ToData(doc),'native_parent':str(native),'saved_at':1794700075,'expected_reject':False}
        records.append({'case':case,'file':case+'.json','sha256':write(output/(case+'.json'),data),
                        'source_request_sha256':sha256((folder/'Request.json').read_bytes()).hexdigest(),
                        'source_prediction_sha256':sha256((folder/'Prediction.json').read_bytes()).hexdigest(),'authored_before_hidden_release':True})
    doc=docs['G01'];graph=doc.assembly;mate=graph.mates[0];child=graph.documents[0].document
    variants={
        'Aligned':replace(doc,assembly=replace(graph,mates=(replace(mate,alignment='aligned'),))),
        'Opposed':replace(doc,assembly=replace(graph,mates=(replace(mate,alignment='opposed'),))),
        'OneParallel':replace(doc,assembly=replace(graph,mates=(replace(mate,kind='parallel',alignment='aligned'),))),
        'OneCoincident':replace(doc,assembly=replace(graph,mates=(replace(mate,kind='coincident',alignment='aligned'),))),
        'ExtraRootMeta':replace(doc,metadata={**doc.metadata,'unprojected':'retained source text'}),
        'ChildCaption':replace(doc,assembly=replace(graph,documents=(replace(graph.documents[0],document=replace(child,metadata={**child.metadata,'environment_caption':'Environment'})),))),
        'MateMetadata':replace(doc,assembly=replace(graph,mates=(replace(mate,attributes={'unprojected':'text'}),))),
        'ScalarValue':replace(doc,assembly=replace(graph,mates=(replace(mate,value=ParameterValue(1.,ValueKind.KLength,'mm')),))),
        'RootParameter':replace(doc,parameters=(Parameter('extra/root','extra',ParameterValue(1.,ValueKind.KLength,'mm')),)),
        'ChildParameter':replace(doc,assembly=replace(graph,documents=(replace(graph.documents[0],document=replace(child,parameters=(*child.parameters,Parameter('extra/child','extra',ParameterValue(1.,ValueKind.KLength,'mm'))))),))),
        'ThirdOccurrence':replace(doc,assembly=replace(graph,instances=(*graph.instances,replace(graph.instances[1],id='instance/2',name=child.metadata['name']+'-3',order=2)))),
        'Unfixed':replace(doc,assembly=replace(graph,instances=tuple(replace(row,fixed=False) for row in graph.instances))),
        'TwoFixed':replace(doc,assembly=replace(graph,instances=tuple(replace(row,fixed=True) for row in graph.instances))),
        'Hidden':replace(doc,assembly=replace(graph,instances=(graph.instances[0],replace(graph.instances[1],hidden=True)))),
        'ExtraEndpoint':replace(doc,assembly=replace(graph,mate_entities=(*graph.mate_entities,replace(graph.mate_entities[0],id='extra/entity')))),
    }
    second=replace(mate,id='mate/second',name='Perpendicular2',order=1)
    variants['SecondPerp']=replace(doc,assembly=replace(graph,mates=(mate,second),mate_groups=(replace(graph.mate_groups[0],mate_ids=(mate.id,second.id)),)))
    second=replace(second,kind='parallel',alignment='aligned')
    variants['MixedPerp']=replace(doc,assembly=replace(graph,mates=(mate,second),mate_groups=(replace(graph.mate_groups[0],mate_ids=(mate.id,second.id)),)))
    sketch=child.sketches[0]
    reordered=replace(child,sketches=(replace(sketch,entities=tuple(reversed(sketch.entities))),))
    permuted=replace(doc,assembly=replace(graph,documents=(replace(graph.documents[0],document=reordered),)))
    for name,document in [('ReorderedEntities',permuted),*variants.items()]:
        document.assert_valid()
        data={'document':ToData(document),'native_parent':str(PureWindowsPath(r'\\Mac\Home\Documents\UniCAD\Oracle121Takeover\PublicPerpendicularRegistry01\GeneratedInput')/(doc.metadata['name']+'.SLDASM')),
              'saved_at':1794700075,'expected_reject':name!='ReorderedEntities'}
        records.append({'case':name,'file':name+'.json','sha256':write(output/(name+'.json'),data),'expected_reject':data['expected_reject']})
    manifest={'schema':'kit.sw2026.private-public-perpendicular-inputs.v1','cases':records,'hidden_values_used':False,
              'production_defaults_unchanged':True,'new_profile_native_qualification':False,'native_processes_started':0}
    digest=write(output/'Inputs.json',manifest)
    print(json.dumps({'cases':len(records),'manifest_sha256':digest,'hidden_values_used':False,'native_processes_started':0},sort_keys=True))


if __name__=='__main__':main()
