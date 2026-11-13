import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.ExactSubtypes import SplineCurve
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import IntcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.ListTsplines import ListTsplines
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ConvertCage import ConvertCage
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ReadStencils import ReadStencils
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

WORK = ROOT / 're/Fusion/LocalOracle/FormDocuments/Stencil'
TARGET = BASE / 'StencilCheck.json'


def gap(left, right):
    if len(left) != len(right):
        return float('inf')
    return max((abs(a - b) for p, q in zip(left, right) for a, b in zip(p, q, strict=True)), default=0.0)


def compare(result, entities):
    found = {item.FaceIndex: item for item in ListTsplines(entities)}
    row = {'surface_max': 0.0, 'curve_max': 0.0, 'point_max': 0.0, 'layout_equal': True, 'jumps_equal': True}
    if sorted(found) != sorted(face.FaceIndex for face in result.Faces):
        row['layout_equal'] = False
        return row
    for face in result.Faces:
        stored = found[face.FaceIndex]
        if (stored.Cache.KnotsU, stored.Cache.KnotsV) != (face.Surface.KnotsU, face.Surface.KnotsV):
            row['layout_equal'] = False
        row['surface_max'] = max(row['surface_max'], gap(stored.Cache.Points, face.Surface.Points))
        if tuple(tuple(item) for item in stored.Jumps) != face.Jumps:
            row['jumps_equal'] = False
    curves = [entity for entity in entities if isinstance(entity, IntcurveNode)]
    points = [entity for entity in entities if isinstance(entity, PointNode)]
    if len(curves) != len(result.Curves) or len(points) != len(result.Points):
        row['layout_equal'] = False
        return row
    for entity, curve, lists in zip(curves, result.Curves, result.CurveJumps):
        stored = SplineCurve(entity.Curve)
        if (stored.Knots, stored.Multiplicity) != (curve.Knots, curve.Multiplicity):
            row['layout_equal'] = False
        row['curve_max'] = max(row['curve_max'], gap(stored.Poles, curve.Poles))
        if tuple(tuple(item) for item in entity.Curve.Body[0][1].Body[7:10]) != lists:
            row['jumps_equal'] = False
    row['point_max'] = gap([entity.PositionCm for entity in points], result.Points)
    return row


def form_entities(path):
    for body in ReadDocument(path.read_bytes()).Bodies:
        if isinstance(body.History, JournalModel) and any(isinstance(e, SplineNode) and isinstance(e.Surface, TsplineSurf) for e in body.History.Entities):
            return body.History.Entities
    raise RuntimeError('no Form body')


def main():
    preparation = json.loads((WORK / 'Preparation.json').read_text())
    probe = json.loads((WORK / 'Probe.json').read_text())
    done = {(cage['cage'], row['variant']): row for cage in probe['cages'] for row in cage['variants'] if row['status'] == 'completed'}
    tables = {table.LayoutKey: table.Label for table in ReadStencils().values()}
    source = ROOT / 'src/convert/formats/Fusion/BrepCodec/Journal/Spline/Stencil/FormStencils.xz'
    report = {'scope': 'Kit stencil conversion of every probe cage against the Fusion conversion stored in the saved archive', 'python': sys.version.split()[0], 'tables_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'cages': []}
    for cage in preparation['cages']:
        name = cage['cage']
        rows = []
        for variant in cage['variants']:
            label = variant['variant']
            probe_row = done.get((name, label))
            tsm = WORK / 'tmp' / name / (label + '.tsm')
            saved = tsm.with_suffix('.f3d')
            if probe_row is None or hashlib.sha256(tsm.read_bytes()).hexdigest() != probe_row.get('tsm_sha256', variant['tsm_sha256']) or hashlib.sha256(saved.read_bytes()).hexdigest() != probe_row['saved_sha256']:
                continue
            try:
                result = ConvertCage(ReadTspline(tsm.read_bytes()))
            except ValueError as error:
                rows.append({'variant': label, 'refused': str(error)})
                continue
            row = {'variant': label}
            row.update(compare(result, form_entities(saved)))
            rows.append(row)
        if not rows:
            continue
        measured = [row for row in rows if 'refused' not in row]
        summary = {'cage': name, 'variants': len(rows), 'refused': len(rows) - len(measured)}
        if measured:
            summary['table'] = 'fitted from this cage' if name in preparation['fitted'] else 'not fitted from this cage'
            summary['surface_max'] = max(row['surface_max'] for row in measured)
            summary['curve_max'] = max(row['curve_max'] for row in measured)
            summary['point_max'] = max(row['point_max'] for row in measured)
            summary['layout_equal'] = all(row['layout_equal'] for row in measured)
            summary['jumps_equal'] = all(row['jumps_equal'] for row in measured)
            summary['jumps_unequal_variants'] = [row['variant'] for row in measured if not row['jumps_equal']]
        else:
            summary['refusal'] = rows[0]['refused']
        report['cages'].append(summary)
        print(json.dumps(summary))
    TARGET.write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
