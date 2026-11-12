import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.modules.pop('LinkCommon', None)
import adsk.core
from LinkCommon import private

app = adsk.core.Application.get()
owned = ('KitLink', 'KitConfig', 'KitAuthored')
report = {'fusion_version': app.version, 'documents_before': app.documents.count, 'open_names': [], 'closed': []}
try:
    for index in range(app.documents.count):
        report['open_names'].append(app.documents.item(index).name)
    for document in [app.documents.item(index) for index in range(app.documents.count)]:
        if document.name.startswith(owned):
            document.close(False)
            report['closed'].append(document.name)
except Exception:
    report['traceback'] = traceback.format_exc()
finally:
    report['documents_after'] = app.documents.count
    (private / 'CloseLinkDocs.json').write_text(json.dumps(report, indent=2) + '\n')
