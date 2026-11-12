import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.ConvertGrid import ConvertGrid
from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import IntcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

SCOPE = 'Kit grid conversion against every converted Form body in local Fusion archives'


def gap(left, right):
    if len(left) != len(right):
        return None
    return max((abs(a - b) for p, q in zip(left, right) for a, b in zip(p, q)), default=0.0)


def compare(result, entities):
    row = {'surfaces': 0, 'curves': 0, 'points': 0}
    worst = 0.0
    for entity in entities:
        if isinstance(entity, SplineNode) and isinstance(entity.Surface, TsplineSurf):
            cache = entity.Surface.Cache
            row['surfaces'] += 1
            if (cache.KnotsU, cache.KnotsV) != (result.Surface.KnotsU, result.Surface.KnotsV):
                raise RuntimeError('knots differ')
            distance = gap(cache.Points, result.Surface.Points)
            if distance is None:
                raise RuntimeError('pole count differs')
            worst = max(worst, distance)
            subtrans = entity.Surface.Subtrans
            if isinstance(subtrans, SubtransNode) and subtrans.Regions != (result.Patches,):
                raise RuntimeError('patch program differs')
        elif isinstance(entity, IntcurveNode):
            cache = entity.Curve.Cache
            matches = [bound for bound in result.Bounds if bound.Knots == cache.Knots and gap(bound.Points, cache.Points) is not None and gap(bound.Points, cache.Points) < 1e-12]
            if len(matches) != 1:
                raise RuntimeError('boundary curve differs')
            worst = max(worst, gap(matches[0].Points, cache.Points))
            row['curves'] += 1
        elif type(entity).__name__ == 'PointNode':
            distance = min(gap((corner,), (entity.PositionCm,)) for corner in result.Corners)
            if distance >= 1e-12:
                raise RuntimeError('corner differs')
            worst = max(worst, distance)
            row['points'] += 1
    row['max_abs_cm'] = worst
    return row


def main():
    files = sorted(str(path.relative_to(ROOT)) for path in (ROOT / 're/Fusion').rglob('*.f3d'))
    rows = []
    for relative in files:
        data = (ROOT / relative).read_bytes()
        try:
            model = ReadDocument(data)
        except Exception as error:
            continue
        if not model.Forms:
            continue
        row = {'file': relative, 'sha256': hashlib.sha256(data).hexdigest()}
        rows.append(row)
        try:
            result = ConvertGrid(model.Forms[0].Surface)
        except ValueError as error:
            row['status'] = 'refused'
            row['reason'] = str(error)
            continue
        try:
            row['members'] = [dict(member=body.PartName.rsplit('.', 1)[-1], **compare(result, body.History.Entities)) for body in model.Bodies if isinstance(body.History, JournalModel)]
            row['status'] = 'equal'
        except RuntimeError as error:
            row['status'] = 'different'
            row['reason'] = str(error)
    summary = {}
    for row in rows:
        summary[row['status']] = summary.get(row['status'], 0) + 1
    report = {'scope': SCOPE, 'python': sys.version.split()[0], 'form_archives': len(rows), 'summary': summary, 'rows': rows}
    (BASE / 'GridCensus.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'rows'}, indent=1))
    for row in rows:
        print(row['status'], row['file'], row.get('reason', ''), [(m['member'], m['surfaces'], m['curves'], m['points'], m['max_abs_cm']) for m in row.get('members', [])])


if __name__ == '__main__':
    main()
