# Automatic native reader verification

The developer CLI now requests native API verification after pinned SOLIDWORKS and Fusion decoding.
`kit run` submits mapped scopes sequentially and verifies completed rescan inputs in application batches.
The controller retains dependencies between scopes, including across pause and resume.
Independent rescans inside one scope can still use multiple offline workers.

## Use

Run the existing `kit research --root CHECKOUT solidworks ...` or `fusion ...` command.
Kit detects the local API before starting an application.
No remote worker configuration is required.

Use `kit research --root CHECKOUT api status solidworks` to inspect SOLIDWORKS availability.
SOLIDWORKS verification requires Windows, the registered licensed COM server, and `pywin32` in Kit's Python environment.
Close existing SOLIDWORKS sessions before verification.
The verifier uses a new session and the existing exclusive oracle mutex.

For Fusion, run `kit research --root CHECKOUT api enable fusion`.
This installs the KitVerify add-in and records hashes for the selected checkout's verifier sources.
In Fusion, enable KitVerify and **Run on Startup** under **Scripts and Add-Ins**.
Close Fusion before you repeat the decoding command.
Kit then launches a fresh local process for each measurement.
An existing application session remains open and blocks verification.
Enable the add-in again after changing verifier sources.

`KIT_NATIVE_API_DIRECTORY` selects an absolute private Fusion verification directory instead of `~/.kit/verification/fusion`.
Use a separate directory for an isolated research host or compatibility run.
When using this option, start Fusion with the same environment setting.
Compatibility tests select an unused directory and cannot attach to a configured user add-in.

## Results

The readers retain their existing `document.json`, `receipt.json`, and Fusion `summary.json` artifacts.
The additional `NativeVerification.json` records the measured input hashes, source revision, application build, controls, cases, and edits.
Catalogue runs retain separate `NativeVerification-solidworks.json` and `NativeVerification-fusion.json` reports.

The native batch performs these operations:

1. Rebuild and measure the pinned healthy control.
2. Open each candidate in a fresh application process.
3. Rebuild and measure bodies, volume, centers, feature history, parameters, and sketch inventories.
4. Compare those observations with the current decoder output.
5. Change each supported independent driving parameter separately.
6. Rebuild, measure, save, and restore the original parameter.
7. Reopen each saved edit in a fresh process and decode that saved file again.
8. Rebuild and measure the final healthy control.

Failed controls invalidate the whole batch.
Changed source code, reused processes, and changed application builds also invalidate acceptance evidence.
Missing decoded measurements cannot pass comparison.
An unavailable API returns setup instructions and leaves verification incomplete.

| Reader exit status | Meaning                                                  |
| ------------------ | -------------------------------------------------------- |
| `0`                | Decoding and requested native reader verification passed |
| `1`                | Input, decoding, or dispatch failed                      |
| `3`                | A Fusion batch contains rejected inputs or reader errors |
| `4`                | The native API needs installation or enablement          |
| `5`                | Native verification failed or its batch was invalid      |

Direct research scripts retain offline decoding unless passed `--native-verify`.
The launcher inspects the selected reader's declared parser options before forwarding that option.
This bounded source inspection does not spawn a capability process or depend on terminal encoding.
Older checkouts still decode their pinned inputs.
They return status `4` after successful decoding and explicitly report that verification was not performed.
Their existing artifacts and Fusion partial-result status remain intact.
The installed developer CLI supplies that option automatically.
Production conversion does not import or invoke these research oracles.

## Scope and limitations

The report identifies its scope as `native_source_reader_verification`.
It compares decoded source documents with their own application observations.
It does not qualify a new writer or a cross-format conversion.
Existing research receipts and conversion markers remain unqualified.
`portable_complete` and `conversion_qualified` remain false.

Current API collectors handle part documents with one to sixteen independent dimensional parameters.
Assembly occurrences and unsupported parameter types fail explicitly.
Absent decoded centers or other required values prevent a passing case.
Native observations retain feature types, but the current common comparison checks names and suppression rather than complete feature definitions.
Sketch comparison checks inventory counts rather than full constraint operands and reference semantics.
Those broader semantic checks remain required before full CAD qualification can be claimed.
The report lists these checks in `semantic_gaps` and keeps `full_semantics_verified` false.
Successful measurement comparisons set `measurement_status` to `passed` but leave the overall status `unverified`.
The command returns status `5` for that incomplete verification.
Consequently, this initial implementation cannot yet certify complete decoding, even with a licensed API available.

Fusion needs its owner-enabled startup add-in to load in the newly launched process.
The protocol requires its PID to match the directly launched process.
A launcher that redirects to another process cannot qualify a case.
Timeouts leave native sessions available for owner recovery instead of closing unrelated documents.

## Verification evidence

Source inspection covered controller dependencies, CLI forwarding, API detection, batch invalidation, and artifact publication.
CLI compatibility coverage now checks missing-API reports and nonzero verification outcomes at the installed process boundary.
Catalogue process coverage inspects the persisted predecessor dependencies and native availability report.
No local tests or licensed application acceptance were executed during implementation.
Remote CI and live licensed SOLIDWORKS and Fusion measurements remain required.
