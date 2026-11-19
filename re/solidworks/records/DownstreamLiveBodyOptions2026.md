# Live downstream body options in SOLIDWORKS 2026

Task `B04-SW2026-DRAWING-DOWNSTREAM-ID` is delivered in [PR #121](https://github.com/TryUniCAD/Kit/pull/121). The [original PE source proof](DownstreamBodyOptions2026.md) derives loader-initial zero at model module RVA `0x2a1681c`. The actual application session now has a separate runtime observation.

From macOS, launch the [probe](../../tooling/sw2026/ProbeDownstreamBodyOptions.py) through `prlctl exec --current-user` in the reserved Windows 11 VM. Supply a path to a disclosed native part, its SHA-256 and a new receipt path. The probe verifies the exact active executable and reads four bytes from the pinned loaded model module's RVA with a read-only process handle. The existing COM helper opens and rebuilds the control in a fresh `SldWorks.Application.34` instance and closes its own process.

| Observation | Option word |
| --- | ---: |
| Startup after versioned COM activation | 0 |
| After ordinary read-only part open | 0 |
| After `ForceRebuild3(False)` | 0 |
| Before closing the measured control | 0 |

The measured process used SOLIDWORKS 2026 SP05.2 build `34.5.2.0604` with the original AMD64 executable and model module hashes. The control passed cleanly with one solid, positive mass volume and 19 feature rows without errors or warnings. There was no native save or option setter call. [Native control receipt](../measurements/2026/DownstreamBodyOptionsLive01.json)

This confirms that the forced vertex and representative-body option bits are clear in the observed ordinary environment. It does not qualify all runtime contexts, output writer behavior or the complete linked drawing lifecycle.
