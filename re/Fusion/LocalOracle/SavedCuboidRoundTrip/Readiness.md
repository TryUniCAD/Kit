# Saved cuboid oracle readiness

The existing [encoder measurements](../../EncoderRoundTrip/NativeEvidence.md)
provide sixteen completed native stage receipts from licensed Windows Fusion
2706.1.17. The four recorded brackets each used four distinct process IDs and
started and ended every stage with zero open documents.

An offline census checked each control and saved archive against the digest
recorded when Fusion opened it. All twelve archives in these four brackets,
including the four independently API-authored controls, carry four axis rules,
two driving linear dimensions, a fixed origin point and a separate fixed
corner at the same coordinates. They also carry one typed snapshot, a typed
graphics scene, and an empty configuration table/rule pair. The baseline
public strict reader stops at the five-rule constrained rectangle guard for
all twelve. This is separate from target-application behavior, which the
earlier receipts measured on the earlier candidate digests.

The new anchor, auxiliary, and reserved held-out capture requests were
prepared in local task scratch. An exact unchanged typed baseline candidate
and its independent control were staged for the same fresh-process lifecycle.
The host showed other Fusion instances and did not provide the sustained
idle interval required by the launcher ownership check. No new Fusion
script was dispatched. Native observations for the new archives remain
unavailable until the capture can run in an isolated session.

The launch guard requires a sustained idle interval and verifies the new
process's ancestry against the launcher it starts. The native script also
requires zero documents on entry. An owned process may be retired after a
failed graceful exit only once its own receipt confirms zero documents.
The host did not pass the idle check, so the launch guard did not start or
retire any Fusion process.

| Replay | Source SHA-256 | Candidate SHA-256 | Independent control SHA-256 |
| --- | --- | --- | --- |
| Baseline reconstruction | `b6726c11bd4e67155035de7fc6bcda3b559682fc9c4f496c2b35a05d84184752` | `c05251997755d8c68a0e8ba14db5ccf248a6ca5b1a610434f51a9801b4d0ce32` | `5f9ad382c5e4b15313a59bebe4201ccd5b87137a3f20ebe85f5e3fba79148ca0` |
| Previously measured holdout role | `5e4552d013a46a603f315fb904cfc62e34c359f1ed9daff51bddd09e3a63eeb7` | `3fba656e80d6a426e0f62908079814df84087cbed5cbb64fae8776cc2b4aa405` | `850b1a76c30c673ba10e33ef1e78618c5e9f106646d5aa9fbf3411ddd6683ac4` |

These candidates came from the experimental typed replay through persisted
strict-read JSON. They have new archive digests. The older native receipts
do not establish how Fusion opens these new bytes.
