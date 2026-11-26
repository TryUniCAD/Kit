# Capture native SOLIDWORKS boss contrasts

The [capture tool](../../../../re/tooling/sw2026/ObserveVendorBossCorpus.py) records native source evidence for one Front-plane line-loop blind boss.
The corpus varies the profile, driving depth and one document property in separate cases.
Two forced saves of the same model show which streams change without a model edit.
The tool also records a separate held-out source from a sealed specification.

## Usage

Use the licensed SOLIDWORKS build and executable digest selected for the experiment.
Supply a vendor part template, a known control part and its authoring record.
Choose an unused output directory.

```powershell
python -B re/tooling/sw2026/ObserveVendorBossCorpus.py --root . capture `
  --output $output --control $control --template $template `
  --executable $executable --executable-sha256 $executableHash
```

Add `--seal-spec` with a separate JSON file to author and verify a single held-out part.
The specification supplies the ordered `profile_m` points and the `depth_m` value.
Keep that specification and its output separate from the discovery cases until the rule is frozen.

The tool opens and rebuilds the control in its own process before authoring.
It reopens each saved file in a fresh process and measures the control again at the end.
It records the executable identity, process lifetime, held-handle exit code and source hashes.
Each observation includes feature nodes, the solid, its driving depth and document property readback.

## Verification and limits

The [corpus record](../../../../re/solidworks/measurements/2026/VendorBossCorpus/SourceContrasts.json) binds the cases to the SOLIDWORKS 2026 SP04.1 executable.
The first discovery batch and the warmed discovery batch each used eight fresh processes.
The separate held-out batch used four fresh processes.
Both controls in each batch passed. Every native process exited with code zero.

The warmed no-op pair retained one encoded self locator and matched the measured geometry.
Nine clear streams changed, including the active partition.
The literal property is a negative case for the existing empty-owner proof.
Its binary property manager grew from 138 to 525 bytes. The exact literal survived fresh reopen.
The baseline reader rounded native driving depths of 13.371 and 21.463 mm to 13.37 and 21.46 mm.

The initial save experiment also found a separate [self-locator behavior](../../../Gotchas/Conversion/Solidworks/Archive/Headers/FirstSaveCanLeaveSelfLocatorEmpty.md).
The corpus measures vendor-authored source files.
It supplies no acceptance evidence for generated output.
