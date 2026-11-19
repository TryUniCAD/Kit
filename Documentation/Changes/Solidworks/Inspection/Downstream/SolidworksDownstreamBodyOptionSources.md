# Downstream body option source ownership

PR #121 adds an independently verifiable source checkpoint for the optional downstream body lane. The pinned original image places its four-byte options word in the PE section's zero-filled virtual tail, giving a derived fresh loader value of zero. An exported whole-word setter is separate from the adjacent enable, lightweight and timing diagnostic callbacks.

The [record](../../../../../re/solidworks/records/DownstreamBodyOptions2026.md) binds complete source owners and hashes, the bit `0x10` body consumers, CRT callbacks, setter name/ordinal and a 31-image normal/delayed import search. The [source receipt](../../../../../re/solidworks/measurements/2026/DownstreamBodyOptionsSource01.json) records 14 complete functions and 29 checked original intervals. The [gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Downstream/Bodies/DownstreamEnableDoesNotSelectBodyOptions.md) preserves the independent state domains.

After staging, run the source-only verifier with a trusted checkout, the licensed pinned original directory and a fresh output path:

```sh
python3 -B re/tooling/sw2026/downstream/VerifyBodyOptionSources.py --root /path/to/Kit --bin-directory /path/to/licensed/pinned/bin --record re/solidworks/records/DownstreamBodyOptions2026.json --output /unused/BodyOptionSources.json
```

No application or vendor module is loaded. The receipt is deterministic. No source payload, instruction listing, CAD file or saved field program is enclosed. The full ordinary application's post-startup word, preference/app-mode policy and native cache acceptance remain open; this addition changes no production behavior and does not enable the body lane.
