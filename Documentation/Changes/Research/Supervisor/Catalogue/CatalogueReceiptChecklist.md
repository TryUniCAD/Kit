# Share SOLIDWORKS catalogue results between devices

SOLIDWORKS catalogue authoring checks committed case records under `re/CatalogueChecklist/` before it queues work.
Each small JSON record identifies one normalized case and its capture evidence.
It can also identify the decoder receipt, status, and counts of unresolved findings and unsupported files.
The exporter writes these records from the run ledger after the run stops.

On a matching capture and reader fingerprint, the runner reports the previous outcome without queuing a job.
If the reader fingerprint changed, the runner can verify an available capture bundle and queue only the offline decoder.
Supply the exported object directory with `--checklist-objects` to enable that path.
Cases with changed capture inputs or missing objects need fresh captures.

Use `--export-checklist` with the run directory to write records to the selected checkout.
Include those records in a regular PR so other devices receive them on pull.
The export can also copy the full receipts, reports, and native capture bundles to an external object directory.
The live ledger and the optional object directory stay outside the checkout.
See the [procedure](../../../../Tasks/ResearchCommandLine.md#share-solidworks-catalogue-results-between-devices).

Use `--fresh-samples` for a fresh native measurement.
The result identifies historical evidence in each reused case.
Unresolved and unsupported results retain their recorded status.
Reused records do not count as fresh native measurements or establish portable conversion acceptance.
The checklist does not coordinate runs that start before a record reaches both checkouts.
This initial workflow covers SOLIDWORKS catalogue authoring.

The [process scenario](../../../../../tests/Research/Inference/Authoring/Recipes/ChecklistFlowTests.py)
exercises two isolated Git checkouts, matching evidence, forced fresh capture, reader invalidation,
offline decoder dispatch, and export of the new receipt.
It uses fixture transport and supplies no licensed native measurement.
