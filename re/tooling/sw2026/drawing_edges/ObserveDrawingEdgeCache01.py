from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys

import DrawingSaveAggregateDbgEng as engine
from DrawingEdgeCacheTrace01 import EdgeCacheTrace, qualified


ORACLE_SHA256 = '3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe'
ENGINE_SHA256 = {
    'dbgcore.dll': 'de03ffb6b1181434c3db61e7ac63e3383b5732ac8a7d28579a30ff306ef8b8c4',
    'dbgeng.dll': '5a2a515f6263c66b0323d8707abf4b64511a9a34f1f1d3fb1f3c4c17f0bf9cad',
    'dbghelp.dll': 'ed7323e007e863dd71e7b405e587969f37e5a146bb0fbcbf885031176bce401d',
    'dbgmodel.dll': '313c4d4b0f0fe4a23f0a8979c83ff40e095828adb4908e1c8869991aefbe6ac9',
    'msdia140.dll': '3499cf0bf1ee71ee04c197c9376fa8438964b557fc172a861572cae21abacd36',
}
SOURCE_IID = '{83A33D34-37C5-11CE-BFD4-00400513BB57}'


def verify_engine(directory):
    engine.require(engine.pe_machine(Path(sys.executable).read_bytes()) == engine.AMD64, 'the owned observer requires existing AMD64 Python')
    for name, expected in ENGINE_SHA256.items():
        engine.check_amd64_image(directory / name, expected)
    return directory / 'dbgeng.dll'


def save_with_edge_trace(controller, author, drawing, target, debugger_directory, *, save_operation=None):
    from OracleIdentity import application_identity

    sw = author.sw
    target = Path(target)
    engine.require(target.name == 'AnnotatedDrawing.SLDDRW' and not target.exists(), 'trace requires an unused exact annotation target')
    identity = application_identity(controller.app)
    engine.require(identity['process_id'] == controller.process_id and controller.process_handle is not None
                   and sw.owned_process_ids() == {controller.process_id} and identity['version_matches']
                   and identity['sha256'] == ORACLE_SHA256 and identity['file_version'] == '34.5.2.0604'
                   and identity['pe_machine'] == hex(engine.AMD64), 'trace requires the exact fresh COM-owned oracle')
    engine_path = verify_engine(Path(debugger_directory))
    trace = EdgeCacheTrace(sw, engine_path, identity)
    source = author.interfaces.DrawingDoc.default_source
    engine.require(str(source.CLSID_Sink).upper() == SOURCE_IID, 'drawing event source differs')
    dispatch = getattr(source, '_dispid_to_func_', {}) or {}
    engine.require(all(dispatch.get(ordinal) == name for ordinal, name in [(7, 'OnFileSaveAsNotify'), (9, 'OnSaveToStorageNotify'), (28, 'OnSaveToStorageStoreNotify')]), 'drawing event ordinals differ')
    timeline = []

    class SaveEvents(source):
        def __init__(self, native):
            source.__init__(self, native)

        def append(self, ordinal):
            if trace.save_entered.is_set() and not trace.save_returned.is_set():
                timeline.append([ordinal, trace.event_offset()])
                if ordinal == 7:
                    trace.result['event7_offset_ns'] = timeline[-1][1]
                    trace.event7_seen.set()
            return 0

        def OnFileSaveNotify(self, *_):
            return self.append(6)

        def OnFileSaveAsNotify(self, *_):
            return self.append(7)

        def OnSaveToStorageNotify(self, *_):
            return self.append(9)

        def OnSaveToStorageStoreNotify(self, *_):
            return self.append(28)

    sink = SaveEvents(drawing)
    status = None
    trace.thread.start()
    try:
        engine.require(trace.ready.wait(engine.SETUP_SECONDS + 2), 'source observer setup exceeded its deadline')
        engine.require(trace.result['armed'], trace.result.get('failure') or 'source observer did not arm')
        operation = controller.save_as if save_operation is None else save_operation
        status = trace.call_owned_save(operation, (author.model, target))
    finally:
        try:
            result = trace.finish()
            sw.pythoncom.PumpWaitingMessages()
        finally:
            sink.close()
        result['save_events'] = list(timeline)
        result['engine_sha256'] = ENGINE_SHA256
        result['observer_method_sha256'] = sha256(Path(__file__).read_bytes()).hexdigest()
        evaluation = qualified(result)
        author.rec.data['drawing_edge_cache_trace'] = result
        author.rec.data['drawing_edge_cache_evaluation'] = evaluation
        author.rec.flush()
        engine.require(result['cleanup_confirmed'] and evaluation['observer_completed_cleanly'], 'source observer did not prove clean owned detach and restoration')
    return status, result, evaluation
