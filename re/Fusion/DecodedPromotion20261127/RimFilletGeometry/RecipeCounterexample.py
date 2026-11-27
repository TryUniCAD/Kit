from pathlib import Path
from dataclasses import replace
import hashlib,json
from RimRecipe import recipe_witness
from RimSource import read_source
from RimState import shape_state
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Circular.DualSides.ReadDualLive import ReadDualLive
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField

root=Path.cwd();folder=Path(__file__).parent;source=root/'re/Fusion/RimFilletPack/Sources/discovery-01/Native.f3d';raw=source.read_bytes();model=ReadDocument(raw);graph=BuildGraph(model);bottom=model.Snapshots[0].Snapshot.TagSet.BottomFace
changed=model;changed_ids=[]
for node in graph.ByClass('ASMRecipe'):
 value=node.Fields['m_Recipe'];encoded=getattr(value,'Value',None)
 if type(getattr(encoded,'Payload',None)).__name__!='EdgeRecipe':continue
 topindex=encoded.Payload.AdjacentFaces[1].PrimaryTagIndex;original,=encoded.Tags[topindex];tags=list(encoded.Tags);tags[topindex]=(replace(original,PrimaryId=tuple(bottom.PrimaryId.encode('ascii')),OperationIds=bottom.OperationIds),)
 changed=ChangeField(changed,node.ObjectId,'m_Recipe',replace(value,Value=replace(encoded,Tags=tuple(tags))));changed_ids.append(node.ObjectId)
assert len(changed_ids)==2
payload=EmitParsed(changed);target=folder/'CoherentWrongAdjacentFace.f3d';target.write_bytes(payload);model=ReadDocument(payload);graph=BuildGraph(model);feature=graph.OneClass('DcFilletEdgeFeature');prior=ReadDualLive(model.Bodies[0].History,feature.Fields['startModelHS']);s=read_source(graph,model,prior);roles=shape_state(prior,s['radius'],s['height'],0.)
try:recipe_witness(prior,roles,s);passed=False
except AssertionError:passed=True
report=dict(case='coherent selection and duplicate progenitor recipe point top-edge adjacent face to bottomcap',models=False,native_calls=0,source_sha256=hashlib.sha256(raw).hexdigest(),candidate=target.name,candidate_sha256=hashlib.sha256(payload).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),recipe_sha256=hashlib.sha256((folder/'RimRecipe.py').read_bytes()).hexdigest(),emitted=True,typed_reparsed=True,source_primary_edge_binding_passed=True,full_geometry_passed=True,complete_recipe_witness_refused=passed)
(folder/'RecipeCounterexample.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report))
