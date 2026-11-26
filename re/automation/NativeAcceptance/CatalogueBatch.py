from functools import partial
import json

from Ledger import Ledger
from NativeAcceptance.Records import ReadBytes
from NativeAcceptance.VerifyBatch import VerifyBatch


def VerifyCatalogue(root, directory, results):
    grouped = {}
    with Ledger(directory / "Store") as state:
        for scope, result in results.items():
            if result["status"] != "completed":
                continue
            for job in result["jobs"]:
                if job["kind"] != "inference.rescan":
                    continue
                row = state.db.execute("SELECT definition,snapshot FROM jobs WHERE id=? AND state='completed'", (job["id"],)).fetchone()
                if row is None:
                    raise ValueError("completed catalogue scope changed before native verification")
                definition = json.loads(row["definition"])
                snapshot = json.loads(row["snapshot"])
                pin = snapshot["inputs"]["source"]["sha256"]
                if pin != definition["options"]["source_sha256"]:
                    raise ValueError("catalogue source pin differs from its completed rescan")
                state.objects.verify(pin)
                application = "solidworks" if definition["options"]["source_format"] == "solidworks.sldprt" else "fusion"
                grouped.setdefault(application, {})[pin] = {"path": scope + ":" + pin, "sha256": pin, "load": partial(ReadBytes, state.objects.path(pin))}
    reports = {}
    for application, samples in sorted(grouped.items()):
        reports[application] = VerifyBatch(root, application, list(samples.values()), directory / f"NativeVerification-{application}.json")
    return reports
