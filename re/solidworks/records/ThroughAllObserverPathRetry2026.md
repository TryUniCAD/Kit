# Through-all native observer path retry

The first generated through-all trial stopped before launching SOLIDWORKS. This is an observer failure, not a native cut result.

Task `B04-SW2026-EXTRUDE-THROUGHALL` remains owned by `/root/assembly_occurrence`, with `/root` the sole VM owner. Delivery is PR #121. Constructor, neutral recipe, predictions and native acceptance checks remain unchanged. Exit requires a complete clean native lifecycle with healthy control brackets, then the separate held-out method.

## Original failure

Original packet SHA-256: `e4933c6d20d4ca4aa597512a850197b05dc2b15677d21de6cbdb2b755941a839`. Observer SHA-256: `b291485f66e5e789196d0ab82d08a75aa6f0dbd063161243c886ab0f56ec7bd2`.

File hashes use relative POSIX keys such as `Control/ThroughAllD01CutForward.SLDPRT`. The old observer computed a lookup key with `str(input_file.relative_to(root))`. Windows produced backslashes, so the dictionary lookup failed before the idle guard or application launch. Both control records remained at `starting`, with zero API calls, zero numeric checks and no result or native identity. The old summary then indexed the absent `result` key.

The [sanitized failure receipt](../measurements/2026/ThroughAllObserverPreflightFailure01.json) binds both original partial records and the successful registered metadata check. Native controls were unmeasured. The generated candidate was never opened. Packet01, metadata and raw records remain unchanged.

## Frozen observer-only retry

Packet02 SHA-256: `b390c68864a8508316d7badd4b43c7643c3dffbcac9ba797fac21a4eb417ab3b`. Recipe SHA-256: `65c768b6d0d41375adcafb7004a1a2494ea135e432a4346ad10258d195e9cd26`. New observer SHA-256: `7119d2a9f9bf14c67c0ef15712a8e72d1d294ae5d83d82949e20e969b18234be`.

The observer uses the declared packet key directly and rejects platform-dependent serialized keys. Packet02 contains byte-identical input and prediction copies. It explicitly opens the original immutable Packet01 native paths. This preserves G01's exact encoded self pathname. Only edited saves and new observations go under Packet02. The original packet and file hashes are rechecked before each phase.

`snapshot`, `native_case`, `api_metadata` and `ui_tree` retain exact AST fingerprints. The constructor source closure, G01's 8497 bytes and complete SHA-256 `5cefc9124919cb2d75a141610fa40a23c328d41297eba6aefe4bcb9f185a3115` are unchanged. No tree, geometry, driver, owner, control, save or warning gate was relaxed.

Partial, missing and malformed phase records now produce an incomplete failed summary. No numeric checks means `not_run`, never a passing empty check set. Native identities count only when both process ID and creation FILETIME were actually recorded.

The [host preflight](../measurements/2026/ThroughAllObserverRetryHost01.json) passed three real observer CLI processes: valid frozen-packet verification, the two captured partial controls with missing phases, and a malformed record. Both incomplete summaries returned failure without a secondary exception. This work started no native process and read no hidden payload.

The [retry freezer](../../tooling/sw2026/PrepareThroughAllRetry.py) independently reproduces the exact existing Packet02 in check mode:

```sh
uv run --isolated --frozen --extra dev --python 3.11 python -B re/tooling/sw2026/PrepareThroughAllRetry.py --prior-root /path/to/GeneratedThroughAll01 --prior-sha256 e4933c6d20d4ca4aa597512a850197b05dc2b15677d21de6cbdb2b755941a839 --observer re/tooling/sw2026/InspectThroughAllCold.py --output /path/to/GeneratedThroughAll02 --check
```

The VM owner runs the immutable recipe serially. The independent trailing control is still required after any candidate failure. Packet02 subsequently passed all four native phases and 72 checks, with both controls healthy. [Scoped native result](SdkThroughAllCutNative2026.md). Original held-out and public registration conclusions remain pending.
