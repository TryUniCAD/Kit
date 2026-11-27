# Draft reader compatibility across the rim-filleting merge

All 68 original draft/control source archives produce byte-identical complete strict SDK document JSON across the two pinned readers. This is an offline reader compatibility result, not conversion or native application acceptance.

| Reader | Exact Git revision |
| --- | --- |
| Previous | `f34820a9d87ac34ca01bd2c5f59cbf6af37f93df` |
| Current merged | `bcabfa069ab3dd0547e031341ec547aefe255b68` |

`Comparison.json` and `Inputs.json` copy the successful `Verified` run's compact records. Every original archive is verified against its committed Git blob, the pre-existing campaign SHA-256, and the other checkout's identical blob. Both tracked source trees were clean before and after execution; unrelated pre-existing untracked SOLIDWORKS CAD files were preserved. Exact source-tree object IDs and interpreter hashes are recorded.

The successful run used 136 distinct fresh Python 3.14.6 processes, one per source per reader, with two concurrent workers and `PYTHONHASHSEED=0`. Each worker imported the intended pinned SDK and called `open_document(BytesIO(payload), strict=True)`, validated the document, and retained the **unmodified** `document.to_json()` UTF-8 bytes. The actual SDK virtual source path is the empty string; it is retained, not deleted or rewritten. No checkout path enters the source document. All 136 reads strictly accepted; all 68 exact byte comparisons passed; there were zero changed documents, strict refusals or reader errors in the successful run, which took 84.56899729196448 seconds.

`Audit.json` independently rechecks committed/working archive equality, exact code revisions/source trees, clean tracked state, source/script/interpreter bindings, all document hashes and lengths, valid JSON, 136 unique worker PIDs and exact old/new document bytes. That final custody verifier uses explicit failure conditions rather than optimizable assertions. The successful worker source is retained verbatim as `CompareDraftsFinal.py`; its script hash is bound in every receipt. No fields, signed zeros or metadata are normalized before comparison.

## Retained invocation failures

`Failures.json` distinguishes every setup/export failure from the successful result. The initial `Run` used the invalid SDK format ID `fusion`; the canonical ID is `fusion.f3d`. `ProbeV2` supplied a placeholder expected digest, which the source guard rejected. `ProbeCorrect` successfully opened the source but incorrectly required `None` instead of the SDK's actual empty source path. The earlier `Final` run exported all 136 document JSON files but an optional receipt counter referenced `features` instead of `feature_timeline`; its error receipts are retained and excluded from the final accepted counts. `ProbeConfirmed` then passed before the complete corrected run began. Exact historical script bytes are kept under `HistoricalSources`.

All per-case documents, receipts and any logs from successful and failed attempts are losslessly packaged in `Documents.tar.gz`. `DocumentArchive.json` records each original relative member path, exact size and SHA-256. Extract in this directory to recover the logical paths, including `Verified/Documents`, `Verified/Receipts`, earlier failed runs and probes. No CAD files or vendor binaries are copied into this package; existing committed source assets are referenced by hash. Published JSON and archive members were checked for private home paths. Models, CAD API calls, native applications and oracle leases were unused.

To reproduce with unused output storage and trusted checkouts containing the exact Git revisions:

```sh
python3 CompareDraftsFinal.py --old /trusted/previous-checkout --new /trusted/current-checkout --output /tmp/UnusedDraftComparison
python3 AuditComparison.py --old /trusted/previous-checkout --new /trusted/current-checkout --run /tmp/UnusedDraftComparison
```

The full decoded read/write programme's writer construction, target lifecycle acceptance, CI/review and other outstanding feature families remain separate requirements. This comparison does not qualify a native output merely because an input decoded successfully.
