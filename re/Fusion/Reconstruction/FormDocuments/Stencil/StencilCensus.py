import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE))
from StencilCheck import compare
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ConvertCage import ConvertCage
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ReadStencils import ReadStencils
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilKey import StencilKey
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

TARGET = BASE / 'StencilCensus.json'
SLACK = 1e-12


def bodies(model):
    return [body.History.Entities for body in model.Bodies if isinstance(body.History, JournalModel) and any(isinstance(e, SplineNode) and isinstance(e.Surface, TsplineSurf) for e in body.History.Entities)]


def main():
    tables = {table.LayoutKey: table.Label for table in ReadStencils().values()}
    stencil = ROOT / 'src/convert/formats/Fusion/BrepCodec/Journal/Spline/Stencil/FormStencils.xz'
    report = {'scope': 'Kit stencil conversion of the cage of every local Form archive against its stored converted body; probe outputs in ignored folders excluded', 'python': sys.version.split()[0], 'tables_sha256': hashlib.sha256(stencil.read_bytes()).hexdigest(), 'slack_cm': SLACK, 'totals': Counter(), 'archives': []}
    seen = set()
    for path in sorted(ROOT.glob('re/Fusion/**/*.f3d')):
        relative = path.relative_to(ROOT)
        if 'tmp' in relative.parts:
            continue
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        try:
            model = ReadDocument(data)
        except Exception:
            continue
        if len(model.Forms) != 1:
            continue
        surface = model.Forms[0].Surface
        row = {'file': str(relative), 'sha256': digest, 'table': tables.get(StencilKey(surface))}
        found = bodies(model)
        if row['table'] is None:
            row['status'] = 'refused'
        elif not found:
            row['status'] = 'no body'
        else:
            checks = [compare(ConvertCage(surface), entities) for entities in found]
            row['gap_cm'] = max(max(item['surface_max'], item['curve_max'], item['point_max']) for item in checks)
            row['layout_equal'] = all(item['layout_equal'] for item in checks)
            row['jumps_equal'] = all(item['jumps_equal'] for item in checks)
            row['status'] = 'equal' if row['layout_equal'] and row['jumps_equal'] and row['gap_cm'] <= SLACK else 'different'
        report['totals'][row['status']] += 1
        if row['table'] is not None:
            report['totals']['table ' + row['table']] += 1
        report['archives'].append(row)
    report['totals'] = dict(sorted(report['totals'].items()))
    TARGET.write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report['totals']))
    for row in report['archives']:
        if row['status'] in ('equal', 'different'):
            print(row['status'], row['table'], row['file'], row.get('gap_cm'))


if __name__ == '__main__':
    main()
