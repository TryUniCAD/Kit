import argparse
import dataclasses
import hashlib
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser(description='Replay the existing source-free circular rim fillet writer and typed read/write codecs')
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--cases', type=Path, required=True)
parser.add_argument('--case', required=True)
parser.add_argument('--directory', type=Path, required=True)
args = parser.parse_args()
root = args.root.resolve(strict=True)
sys.path.insert(0, str(root / 'src'))
from convert.Formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.CircleCurve import CircleCurve
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import ExtrudeSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import FilletSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.SolvePart import SolvePart
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Design.PartTopology import MeasurePart

cases = json.loads(args.cases.read_bytes())['cases']
selected = [case for case in cases if case['id'] == args.case]
if len(selected) != 1:
    raise ValueError('case identity must select exactly one predefined input')
case = selected[0]
features = (
    ExtrudeSpec((CircleCurve((0.0, 0.0), case['radius_mm']),), case['height_mm'], SketchName='Disc sketch', FeatureName='Disc extrude'),
    FilletSpec((case['radius_mm'], 0.0), case['fillet_mm'], 'Rim round', LevelMm=case['height_mm']),
)
spec = DocumentSpec('Kit rim fillet', 'height', case['height_mm'], ProfileKind='part', BodyName='Body1', Features=features)
_, stages = SolvePart(spec)
metrics = dataclasses.asdict(MeasurePart(stages[-1].After))
payload = EmitDocument(spec)
model = ReadDocument(payload)
reconstructed = EmitParsed(model)
if ReadDocument(reconstructed) != model:
    raise ValueError('typed writer reconstruction changed the complete decoded model')
args.directory.mkdir(parents=True, exist_ok=False)
(args.directory / 'Generated.f3d').write_bytes(payload)
(args.directory / 'Reconstructed.f3d').write_bytes(reconstructed)
result = dict(case=case, geometry=metrics, model_equal=True, generated_sha256=hashlib.sha256(payload).hexdigest(), reconstructed_sha256=hashlib.sha256(reconstructed).hexdigest(), byte_equal=payload==reconstructed, contract='source-free constructor plus typed same-document reconstruction; neutral conversion remains unqualified', native_acceptance=False)
(args.directory / 'Replay.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result))
