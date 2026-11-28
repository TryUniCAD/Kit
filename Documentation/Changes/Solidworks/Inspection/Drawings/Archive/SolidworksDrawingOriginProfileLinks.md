# SOLIDWORKS drawing origin-profile linkage observations

The hash-bound inspection tool follows a retained drawing profile display through its actual component chain and external reference into the complete linked child Header/Config/CMgr/Resolved graph. It reports concrete profile ownership, persistent IDs, creation logs and source/output lifecycle differences without selecting by names or changing the SDK.

Run `re/tooling/sw2026/InspectDrawingProfileChild.py CANDIDATE PAIRS OUTPUT --manifest-sha256 SHA --pairs-sha256 SHA` with an immutable SDK candidate, the exact four-pair custody manifest and an unused output path. The tool verifies source/input hashes before and after execution. Metadata inspection does not launch SOLIDWORKS.

Both disclosed original displays resolve to the child origin, which is a native profile subclass. Their generated pairs lack this display both initially and after their already measured native saves. Initial and saved-state reports passed all eight complete drawing byte comparisons and all child graph loads. [Rules and exact hashes](../../../../../../re/solidworks/records/DrawingOriginProfileLinkage2026.md), [sanitized receipt](../../../../../../re/solidworks/measurements/2026/DrawingOriginProfileLink01.json), [class-identity gotcha](../../../../../Gotchas/Conversion/Solidworks/Drawings/Qualification/ProfileDisplaysCanReferenceChildOrigins.md).

The existing original writer, strict public drawing guard, unprojected profile marker and failed original held-out verdict are unchanged. This tool supplies observations; fresh generation and independent qualification remain pending.
