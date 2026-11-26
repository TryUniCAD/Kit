import hashlib
import json
from pathlib import Path

from NativeAcceptance.Assessment import AssessChecks
from NativeAcceptance.CompareDocument import CompareDocument
from NativeAcceptance.Records import ReadBytes, WriteJson


def CompareFile(application, document_path, measurement_path, output):
    from interchange.document.Models.DocumentModel import CadDocument

    output = Path(output)
    if output.resolve() in (Path(document_path).resolve(), Path(measurement_path).resolve()):
        raise ValueError("comparison output must not replace either input")
    source = ReadBytes(document_path, 64 * 1024 * 1024)
    observation = ReadBytes(measurement_path, 16 * 1024 * 1024)
    document = CadDocument.from_json(source.decode("utf-8"))
    document.assert_valid()
    native = json.loads(observation)
    if not isinstance(native, dict):
        raise ValueError("comparison measurement must be a JSON object")
    checks = CompareDocument(document, native, application)
    report = {"schema": 1, "application": application, "scope": "offline_measurement_comparison", "native_acceptance": False, "live_batch_verified": False, "portable_complete": False, "conversion_qualified": False, "document_sha256": hashlib.sha256(source).hexdigest(), "measurement_sha256": hashlib.sha256(observation).hexdigest(), "checks": checks, **AssessChecks(checks)}
    WriteJson(output, report)
    return report
