import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE.parent / 'NativeAcceptance.json'
VARIANTS = Path(tempfile.gettempdir()) / 'KitFusionDrawings' / 'Variants'
GUID = re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')
PRIVATE = ('/Users/', '/var/folders/', 'Library/Application Support', 'AppData', 'urn:adsk', 'W.login')


def load(name, fallback=None):
    path = Path(name) if Path(name).is_absolute() else VARIANTS / name
    if not path.exists():
        return fallback
    return json.loads(path.read_text())


def view(row):
    keep = {'type': row.get('type'), 'curve_count': row.get('curve_count')}
    for key in ('orientation', 'scale', 'style'):
        value = row.get(key)
        keep[key] = value if not isinstance(value, dict) else 'getter failed'
    keep['curves'] = row.get('curves', [])
    return keep


def drawing(info):
    if not isinstance(info, dict) or 'sheets' not in info:
        return info
    sheets = []
    for sheet in info['sheets']:
        sheets.append({'name': sheet.get('name'), 'width_mm': sheet.get('width'), 'height_mm': sheet.get('height'), 'dimensions': sheet.get('dimensions'), 'title_block': sheet.get('title_block'), 'views': [view(row) for row in sheet.get('views', [])]})
    return {'title_blocks': info.get('title_blocks'), 'sheets': sheets}


def opened(row):
    if not isinstance(row, dict):
        return row
    result = {key: row[key] for key in ('ready', 'references', 'modified_after_open', 'open_error', 'missing_folder') if key in row}
    result['files'] = [{key: item[key] for key in ('name', 'extension', 'version', 'complete')} for item in row.get('files', [])]
    if 'opened' in row:
        result['drawing'] = drawing(row['opened'])
    result['captures'] = [{'file': GUID.sub('<guid>', Path(item['cache_relative']).name), 'bytes': item['bytes'], 'sha256': item['sha256']} for item in row.get('captures') or []]
    return result


def inspection(report):
    if report is None:
        return {'status': 'not run'}
    return {'status': report.get('status'), 'stage': report.get('stage'), 'documents_after': report.get('documents_after'), 'uploads': {label: opened(row) for label, row in report.get('uploads', {}).items()}}


def edit(report):
    if report is None:
        return {'status': 'not run'}
    keys = ('status', 'stage', 'design_before', 'design_after', 'references_before', 'update_result', 'references_after', 'drawing_version', 'read_only', 'save_requests', 'documents_after')
    result = {key: report.get(key) for key in keys if key in report}
    result['drawing_before'] = drawing(report.get('drawing_before'))
    result['drawing_after'] = drawing(report.get('drawing_after'))
    if 'reopened' in report:
        result['reopened'] = {**report['reopened'], 'drawing': drawing(report['reopened'].get('drawing'))}
    if 'traceback' in report:
        result['error'] = report['traceback'].strip().splitlines()[-1]
    result['captures_saved'] = [{'file': GUID.sub('<guid>', Path(item['cache_relative']).name), 'bytes': item['bytes'], 'sha256': item['sha256']} for item in report.get('captures_saved') or []]
    return result


def steps(report):
    if report is None:
        return {'status': 'not run'}
    rows = [{key: row.get(key) for key in ('name', 'started', 'finished', 'status', 'documents_after')} for row in report.get('steps', [])]
    waits = report.get('upload_waits') or ([report['upload_wait']] if 'upload_wait' in report else [])
    return {'status': report.get('status'), 'documents_after': report.get('documents_after'), 'upload_waits': waits, 'steps': rows}


def capacity(report):
    if report is None:
        return {'status': 'not run'}
    keys = ('status', 'before', 'blocked', 'needed', 'deleted', 'stopped', 'after', 'watched_after', 'documents_after')
    result = {key: report.get(key) for key in keys if key in report}
    result['watched_before'] = report.get('watched_before')
    if 'traceback' in report:
        result['error'] = report['traceback'].strip().splitlines()[-1]
    return result


def main(extra):
    plan = load('Plan.json')
    report = {
        'schema': 'KitFusionDrawingNativeAcceptance/1',
        'fusion_version': '2706.1.17',
        'variants': plan['variants'],
        'inputs': plan['inputs'],
        'historical': plan['historical'],
        'modern_typed': plan.get('modern'),
        'controls': inspection(load(extra.get('controls', 'InspectControls.json'))),
        'typed_reemission': inspection(load('InspectM1.json')),
        'edit_acceptance': edit(load('EditM1Reemitted.json')),
        'views_control': inspection(load('InspectP4.json')),
        'no_database': inspection(load('InspectP2.json')),
        'swapped_database': load(extra['stall']) if 'stall' in extra else None,
        'missing_database': load(extra['missing']) if 'missing' in extra else None,
        'reverse_swap': inspection(load('InspectP5.json')),
        'capacity': {'attempt1': capacity(load('CapacityAttempt1.json')), 'attempt2': capacity(load('Capacity.json.report.json'))},
        'saved_edit': {'attempt1': edit(load('EditM2Attempt1.json')), 'attempt2': edit(load('EditM2Reemitted.json'))},
        'runs': {'typed': steps(load('AcceptTyped.json')), 'saved': steps(load('AcceptSaved.json')), 'saved2': steps(load('AcceptSaved2.json'))},
        'fixtures': json.loads((BASE.parent / 'Fixtures.json').read_text()),
    }
    report.update(json.loads(Path(extra['notes']).read_text()) if 'notes' in extra else {})
    text = json.dumps(report, indent=1, default=str) + '\n'
    leaks = [token for token in PRIVATE if token in text]
    if leaks:
        raise ValueError('Private tokens in acceptance report: ' + ', '.join(leaks))
    OUT.write_text(text)
    print(OUT.name, hashlib.sha256(text.encode()).hexdigest())


if __name__ == '__main__':
    main(dict(item.split('=', 1) for item in sys.argv[1:]))
