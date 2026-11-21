from pathlib import Path
from hashlib import sha256
import json,sys
from codecs import lookup
sys.dont_write_bytecode=True
root=Path(sys.argv[1]);mode=sys.argv[2];sys.path.insert(0,str(root/'src'));sys.path.insert(0,str(root/'re/tooling/sw2026'));sys.path.insert(0,str(root/'re/tooling/sw2026/throughowners'))
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.MakeThruOwners import MakeThruOwners
from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import FeatureInstant
from OwnerDto import decode,settings
from OwnerFragments import emit,identities
from OwnerGuard import OwnerGuard
if mode=='baseline':
 from downstream.lighting.AmbientInput import AmbientInput
 from downstream.lighting.AttachAmbientMut import AttachAmbientMut
else:
 from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import LightInput
 from convert.adapters.solidworks.Archive.Construction.System.Members.MakeLightMut import MakeLightMut
for codec in ('utf-16-le','utf-8','ascii','latin-1'):lookup(codec)
request=json.load(sys.stdin);guard=OwnerGuard();sys.addaudithook(guard.inspect);guard.active=True
value=decode(request['owner_input']);target=settings(value,1795107901);graph=MakeThruOwners(value,target);entry=request['light'];epoch=1795107901
if mode=='baseline':node=AttachAmbientMut(graph.SystemValue.RootValue,AmbientInput(**entry),target.TargetValue,graph.IdsValue,epoch)
else:
 folder=graph.SystemValue.SystemValues.FolderValues['moEnvFolder_c'];light=LightInput('ambient',entry['NameValue'],entry['ExternalName'],entry['AmbientValue'],entry['DiffuseValue'],entry['SpecularValue'],entry['ColourValue'],True,False,True,1.0,True,16.0,None,None,FeatureInstant(epoch,0));node=MakeLightMut(folder,light,target.TargetValue,graph.IdsValue);folder.FieldsValue['f60']={'list':{'n':1,'items':[{'o':node}]},'tail':0}
fragments,_,_=emit(graph,target);guard.active=False;print(json.dumps({'passed':True,'fragments':identities(fragments),'guarded_input_reads':0,'denied_events':guard.denied},sort_keys=True))
