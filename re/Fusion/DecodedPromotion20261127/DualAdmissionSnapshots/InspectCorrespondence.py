import sys
sys.path[:0]=['src','.']
from dataclasses import replace
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases
from tests.Convert.Integration.Fusion.DualSide.ReadDualState import ReadDualState
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import MakeEntityNode
from convert.Formats.Fusion.BrepCodec.Journal.Permutation.RemapEntity import RemapEntity
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import BodyFaces

def canon(st,body):
 st=replace(st,Entities=tuple(replace(e,Prefix=replace(e.Prefix,Attribute=-1)) if isinstance(e,BodyNode) else e for e in st.Entities))
 seen=[next(i for i,e in enumerate(st.Entities) if isinstance(e,BodyNode) and e.FirstLump==body.FirstLump)]
 for i in seen:
  for t,v in MakeEntityNode(st.Entities[i]).Tokens:
   if t==12 and isinstance(v,int) and v>=0 and v not in seen:seen.append(v)
 mapping=tuple(seen.index(i) if i in seen else -1 for i in range(len(st.Entities)))
 rows=[]
 for i in seen:
  e=RemapEntity(st.Entities[i],mapping)
  if hasattr(e,'Prefix'):e=replace(e,Prefix=replace(e.Prefix,EntityTag=-1))
  rows.append(e)
 return rows
import json,hashlib
from pathlib import Path
rows=[]
for s in ReadDualCases():
 row={'source':str(s.Source.relative_to(Path.cwd())),'sha256':s.Digest,'holdout':s.Identity.startswith('holdout'),'xy':s.Frame.z_axis.z==1.0}
 try:
  m=ReadDocument(s.Source.read_bytes());g=BuildGraph(m);c=SelectExtrusion(g)
  live=ReadDualState(m.Bodies[0].History,c.Extrude.Fields['endModelHS']);snap=m.Snapshots[0].Snapshot
  a=canon(live,next(e for e in live.Entities if isinstance(e,BodyNode)))
  bodies=[e for e in snap.Entities if isinstance(e,BodyNode)]
  solid=next(e for e in bodies if len(BodyFaces(snap,e))>1)
  b=canon(snap,solid)
  row.update(correspondence=a==b,live_solid_nodes=len(a),snapshot_solid_nodes=len(b),body_faces=[len(BodyFaces(snap,e)) for e in bodies],snapshot_entities=len(snap.Entities))
 except Exception as e: row.update(error=type(e).__name__+': '+str(e))
 rows.append(row)
report={'program_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'sources':rows,'summary':{'xy':sum(r['xy'] for r in rows),'xy_matches':sum(r['xy'] and r.get('correspondence',False) for r in rows),'xz':sum(not r['xy'] for r in rows),'errors':sum('error' in r for r in rows)}}
Path(sys.argv[1]).write_text(json.dumps(report,indent=2)+'\n');print(report['summary'])
