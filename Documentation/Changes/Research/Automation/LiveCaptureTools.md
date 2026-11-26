# Live capture tools

The eleven collector and verifier paths that had diverged from the sealed capture tree now live under `re/automation/CaptureTools`. The original tree again contains the recorded files at their original paths. The [capture authoring guide](../../../Reference/Research/SolidWorksCaptureAuthoring.md) and [paired capture guide](../../../Reference/Research/PairedCaptures.md) identify the live launchers.

The supervisor pins live code to its Git revision. Readback verification still checks the source paths, hashes and sizes recorded by the producer. Historical reports keep their original source identities. For the relocated principal readback launcher, verification compares the script to the approved launcher after accounting for its single changed collector-directory declaration.

## Verification

Git comparison against `f5b23031c4163528a2e4f5029ab34102133b983e` found no differences in the sealed inputs. The three relocated Fusion verifier files were byte-identical to their previous versions. The two SOLIDWORKS launcher revisions differed only in the collector-directory declaration. These are source checks. Native application readback requires a separate measured run.
