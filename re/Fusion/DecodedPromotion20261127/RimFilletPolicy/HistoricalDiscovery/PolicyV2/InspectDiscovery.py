import dataclasses
import hashlib
import json
from pathlib import Path
from collections import Counter
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph

root = Path(__file__).resolve().parents[4]
output = Path(__file__).parent / 'Discovery'
output.mkdir(exist_ok=True)
rows = []
for index in range(1, 7):
    path = root / f're/Fusion/RimFilletPack/Sources/discovery-{index:02}/Native.f3d'
    data = path.read_bytes()
    model = ReadDocument(data)
    graph = BuildGraph(model)
    nodes = [dict(segment=n.SegmentId, identity=n.Identity, object_id=n.ObjectId,
                  class_name=n.ClassName, fields=repr(n.Fields),
                  groups=dataclasses.asdict(n)['Groups']) for n in graph.Nodes.values()]
    (output / f'Graph{index:02}.json').write_text(json.dumps(nodes, indent=2, default=repr)+'\n')
    rows.append(dict(source=str(path.relative_to(root)), sha256=hashlib.sha256(data).hexdigest(),
                     classes=dict(Counter(n.ClassName for n in graph.Nodes.values() if n.SegmentId == 0)),
                     asset=model.Asset.AssetId))
(output / 'Receipt.json').write_text(json.dumps(dict(models=False, native_calls=0,
    reserved_opened=False, producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), rows=rows),indent=2)+'\n')
print(json.dumps(rows[0],indent=2))
