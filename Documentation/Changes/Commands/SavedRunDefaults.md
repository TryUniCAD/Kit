# Saved catalogue run defaults

The installed `kit` CLI can read private catalogue defaults without a shell profile.
This supports `kit run solidworks` and `kit run fusion` after their presets are configured.
No preset is supplied by the package.

## Configuration

Save UTF-8 JSON at `~/.kit/RunDefaults.json`.
Alternatively, set `KIT_RUN_DEFAULTS` to a selected JSON file.
The file is limited to 64 KiB.

```json
{
  "schema_version": 1,
  "formats": {
    "solidworks": {
      "root": "C:/Trusted/Kit",
      "output_root": "D:/KitRuns",
      "options": {
        "--catalogue": "C:/Trusted/Kit/re/solidworks/PlannerCatalog/Sources/FeaturePlan.json",
        "--author-samples": true,
        "--capture-mode": "discovery",
        "--authoring-grid": "three-values",
        "--solidworks-host": "C:/Private/SolidWorksHost.json",
        "--native-ready": true,
        "--workers": "18",
        "--reserved-memory-mib": "2048",
        "--max-seconds": "86400"
      }
    }
  }
}
```

Use absolute `root` and `output_root` paths.
Only the current user's `~` home syntax is expanded; named-user home paths are rejected consistently across platforms.
The trusted checkout must contain the selected research implementation and SDK.
Presets explicitly authorize the configured research options, including native dispatch when `--native-ready` is true.
Keep these settings in a private user directory.
Do not put licensed software in the checkout.

Option names must be full long flags in presets and shortcut overrides.
Saved catalogue paths must be absolute, including format-specific catalogue options.
Use strings for values, `true` for enabled switches, and `false` to omit switches.
Explicit command arguments replace the corresponding defaults.
An explicit catalogue path replaces its saved path and saved digest together.
Supply an explicit format-specific digest to pin the replacement file.
Each catalogue invocation generates a unique output directory below `output_root`, unless `--directory` is supplied.

`--input`, `--pause`, `--resume`, and help use only the configured root.
Supply their usual operation arguments, including `--directory` where required.
An explicit `kit run --root CHECKOUT ...` bypasses presets entirely.
Unconfigured formats retain the existing explicit-root requirement.
Other CLI commands do not read this file.

## Verification and limits

Installed-process checks cover both formats, fresh destinations, explicit overrides, operation isolation, malformed presets, and explicit-root recovery.
They run through the existing complete-suite planner and compatibility paths.
Desktop acceptance passed in Windows PowerShell 5.1 with `-NoProfile` and the installed executable.
The real catalogue runner prepared 62 samples using the selected batching checkout at `d2478698bc97864f371b6eef0b7f1745ffa2672d`.
Its plan recorded `solidworks_batch_version: 1`.
This `--prepare-only` check launched no CAD application.
This feature configures startup and does not qualify CAD output or decoder semantics.

Task `B10-RunDefaults`, owned by Codex, depends on the installed CLI bridge and trusted catalogue checkout.
Its exit requires profile-free command verification, current-head CI, and configured review.
Delivery is tracked on [PR #290](https://github.com/TryUniCAD/Kit/pull/290).
Native batching remains owned by [PR #288](https://github.com/TryUniCAD/Kit/pull/288).
