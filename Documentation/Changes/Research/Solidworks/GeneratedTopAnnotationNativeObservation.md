# Measure a generated SOLIDWORKS boss with a Top annotation view

The [native observer](../../../../re/tooling/sw2026/ObserveGeneratedTopAnnotation.py) measures a generated Front-plane blind boss in a sequence of fresh SOLIDWORKS processes. It brackets the experiment with known vendor-authored controls and checks an independently authored boss at the edited depth. It also checks the exact plain generated variant with the same geometry and encoded locator.

The observer opens the original candidate read-only, checks its feature tree, solid and annotation views, and rebuilds it in memory. It edits D1 on a separate byte-identical copy, then saves to a new file. A fresh process opens the saved edit read-only and measures the same geometry and annotation state after rebuild. The lifecycle records bind the input bytes, executable and observed process exits.

## Usage

Supply a plan with the frozen `candidate_revision`, `manifest_path`, `manifest_sha256`, `neutral_request_path`, `oracle_build`, ordered `profile_m` points, `depth_m`, `edit_depth_m`, and an `inputs` map. That map requires `Control`, `EditControl`, `PlainBaseline`, and `Candidate` entries with their exact `path` and `sha256` values. Use an unused output directory and the licensed executable with its expected digest.

```powershell
python -B re/tooling/sw2026/ObserveGeneratedTopAnnotation.py --root . measure `
  --plan $plan --output $output --executable $executable `
  --executable-sha256 $executableHash
```

The intended annotation is one hidden assigned view with the exact Top rotation. The SOLIDWORKS API also reports the built-in unassigned view. The plain negative comparison expects only that unassigned view. These checks cover one research experiment. Whole vendor-source admission and SDK publication require separate evidence.

## Verification

The [native evidence](../../../../re/solidworks/measurements/2026/VendorBossCorpus/GeneratedTopAnnotation.json) retains the original stopped run as well as the continuation. The first run stopped on an exact-bit comparison against the plain baseline's valid driving depth. The continuation used the original plan, archived inputs and already measured controls, with a one-ULP bound for the [unit conversion difference](../../../Gotchas/Conversion/Solidworks/Archive/Configuration/MetreDepthConversionsCanDifferByOneUlp.md).

SOLIDWORKS 2026 SP04.1 `34.4.1.1011` opened and rebuilt the original candidate with zero errors and warnings. It reported two annotation views, including the hidden Top view, and one solid with a volume of 7,584.3 mm³. Changing D1 from 14.31 mm to 19.87 mm produced a volume of 10,531.1 mm³. The saved edit reopened and rebuilt at the new depth with the same feature tree and annotation views. The saved configuration retained a typed `*Top` record with the exact rotation. Each of the eight distinct owned processes exited normally.

For this exact stopped preflight, `--preflight` and `--preflight-sha256` identify the existing result and its digest. The observer verifies the retained per-phase records, inputs, process exits and native measurements before using the latest control as the leading observation. Use the plain invocation for a new campaign.
