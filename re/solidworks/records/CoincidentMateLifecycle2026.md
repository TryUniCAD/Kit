# Coincident mate registration time and update state in SOLIDWORKS 2026

This record follows one ordinary, resolved two-plane `moMateCoincident` owned by a flat `moMateGroup_c` in an unfrozen assembly, at build `34.5.2.0604` and archive version `19000`. All addresses are preferred virtual addresses in the pinned original images. The A17 source comparison is the only saved assembly observed for this supplement. [Registration and archive ownership](CoincidentMatePublication2026.md) · [Image, function and dispatch fingerprints](CoincidentMateLifecycle2026.json)

## Constructor and registered feature

| Field | Native operation |
| --- | --- |
| `f0c` | The generic node constructor initializes the pending-update bit, yielding `1`. The mate's construction and insertion proof establishes that seed. The later group operation below can raise the separate bit `0x100`. |
| `f2a0/f2a4` | The owner-taking feature constructor `0x4bb38350` clears the low and high FILETIME words at `0x4bb386db`. Group insertion invokes the concrete mate's `+0x1590` slot, `moFeature_c::onCreate` `0x4bb4de30`. With the filed owner assigned, the ordinary path reaches the clock sample at `0x4bb4e2af`. It stores high then low at `0x4bb4e2ec` and `0x4bb4e2f9` unless the owner is a model and its document is frozen. The recognized assembly returns true at `+0x198` and takes the unfrozen branch in this scope. A registered mate therefore needs a registration time. |
| `f2b8/f2bc` | The same constructor clears both last-update fields at `0x4bb3855a`. The direct registration tail writes the FILETIME and leaves the last-update fields separate. Initialize the registration-only state to zero and apply the version-mark operation only where the composer models an admitted completed update. |
| `f2b0/f2b4` | The constructor sets the feature's originating version and build date at `0x4bb38554` and `0x4bb3864c`. These are separate from the last-update pair. |

Use the explicit registration epoch with the shared `feature_filetime` conversion. Whole Unix seconds `t` give `(t + 11644473600) * 10000000` FILETIME ticks. Split at bit 32 into low `f2a0` and high `f2a4`. Present each word to the signed integer codec with its original 32 bits. The revision entry separately stores its event time in seconds. A builder can supply the same authored instant to both stores for a single modeled registration event. [Shared constructor and build provenance](ModelConstruction2026.md)

## Bit 8 on the mate

The coincident table `0x4cfa46e0` supplies the inherited getter `+0x230 -> 0x4b28e090` and setter `+0x238 -> 0x4b30f9f0`. The named functions are `moNode_c::isSatNotSolved` and `moNode_c::setSatNotSolved`. The getter returns the masked value `f0c & 0x100`. The setter applies `(f0c & 0xfffffeff) | (0x100 if flag else 0)`. The independent `moMate::setSolveStatus` `0x4b2c7bc0` writes only `+0x3b8`.

`moAssembly_c::assemble` invokes `0x4b6a36d0` at `0x4b687ced`, immediately before the wrapper-ID traversal at `0x4b687cf7`. For a nonnull first mate group with no foreign-owned super group and no skipped update context, `0x4b6a36d0` calls the group's `+0x1138` at `0x4b6a38bd`. The ordinary group table `0x4cfe0028` maps this to `0x4bc8aa40`. The named assembly `doUnsatisfiedAnalysis` also calls this group slot at `0x4b692f7a`. The latter group helper can delegate to a different group. The flat assembly here takes its direct branch.

The direct branch in `0x4bc8aa40` collects group feature pointers with `+0x1ed0`. For the ordinary non-cam member, the call at `0x4bc8ac9b` requires all of the following.

1. The mate eligibility slot `+0x1970` is nonzero. On the coincident receiver `0x4bc5f050` this requires `+0x298 == 0` and also rules out an ineligible containing mate folder. An ordinary group returns false at its `+0xbd8`, so it takes the direct eligible branch.
2. Either `+0x1fa0` is false, or `+0x1fb8` is true. This preserves the native endpoint/context filter.
3. Either `+0x1f70(0,1)` succeeds, or `+0x2090` succeeds with the assembly's current context argument. The first operation can validate and cache the resolved mate geometry. The second inspects whether its endpoint references satisfy the fixed or equivalent context conditions. Neither result follows from the presence of two wrapper pointers alone.
4. The configuration check `+0x2098(active_configuration)` returns zero, and `+0x2108` returns a value other than `1`. The concrete latter leaf `0x4b287740` reads runtime `+0x49c`. The mate constructor clears that word as part of its `+0x498` qword at `0x4bc2dd12`.

The positive branch takes the returned feature from `+0x2010 -> 0x4bc567e0` and supplies integer `1` to its `+0x238`. The receiver helper selects its parent only if the feature owner is itself a `moMateParent`. For the ordinary owning group it returns the original coincident feature. This write precedes the `+0x2020` geometric residual check. The three rejection edges in the coincident residual helper `0x4bc628e0` reach `0x4bc7e520`, which clears the same bit with argument zero at `0x4bc7e686` and can report a diagnostic. Passing the check can preserve the set bit.

The group's independent `clearUpdateFlags` at `0x4bc890f0` calls each collected mate's `+0xb8` with `(0,1,null)` at `0x4bc89147`. On the coincident table this is the feature override `0x4bb515c0`, which reaches the node update operation at `0x4bb51695`. Its zero-status mask `0xfffd7ff8` clears the initial bit 0 and retains bit 8. From seed `1`, applying this clear and the admitted positive operation yields `0x100` in either order, provided no later clear or independent bit mutation intervenes. The numeric flag is the result of these operations. No suppressed-configuration flag is involved.

## Rebuild marks and archive behavior

The assembly update helper `0x4b6a4a50` can call the group's `0x4bc92fd0` at `0x4b6a6770` for the group entries admitted by its traversal boundaries. That function enumerates with group `+0x1ec0`, requires each mate's `+0x1970` and `isMateValidForGraphicsComp() == 1`, then calls the mate's `+0x1f08`, a return-only leaf for this class. At `0x4bc93075` it invokes `+0x15e8 -> moFeature_c::postUpdate` `0x4c1ce660` with force zero.

The mate inherits two independent update operations.

- Forced stamping or the non-forced needs-update and lock checks, together with a nonnull filed owner, lead to `0x4bb4a4b0` at `0x4c1ce756`. This sets `f29c` from the current owner header stamp and may replace the feature FILETIME, with the same frozen-document guard. For the ordinary coincident receiver and group, `needsUpdate(0)` reaches the node test at `0x4c03e5e4` and tests bit 0. A non-forced call after clearing that bit leaves the registration time intact.
- At `0x4c1ce75b`, the version-mark branch requires either `feature+0x26c & 2` or a nonnull filed owner with true virtual `+0x1a8`. The assembly returns true at that slot. A reached `postUpdate` therefore assigns both `f2b8 = current target file version` and `f2bc = target full build date code` at `0x4c1ce79d` and `0x4c1ce7a9`. The pinned manager and tagged-date inputs are `19000` and `2026306`. This path can mark the version without sampling a new time.

The normal mate serializer passes through `moMateParent::Serialize` and `moModelFeature::Serialize` to `moFeature_c::Serialize` at `0x4bb11aa0`. For the selected modern version the store takes the live last-update words directly at `0x4bb11bf2` and `0x4bb11c01`. The `>= 0x1dd` reader fills them from the archive at `0x4bb121c8` and `0x4bb121d8`. At version `>= 0x11cd` the store takes the live FILETIME high word then low word at `0x4bb11eaf` and `0x4bb11ebe`. The modern reader consumes the same order at `0x4bb129ae` and `0x4bb129bc` and supplies them to `setFeatTimeStampForConfigs`. Its load-time repair samples the clock if the live high word is still zero after that operation. The ordinary node store writes its live `f0c` word. These store operations do not compute the registration time, last-update version or bit 8.

## Disclosed comparison and limits

A17 mate ID `26` stores `f0c=0x100`, independent `f3b8=1` and `f29c=101`. Its feature FILETIME decodes to `2026-11-17T09:26:03.2549612Z`. Both revision-log mirrors store the same whole second, `1794907563`. This is consistent with registration time surviving the reached updates. It does not establish the order of native clock samples within that second. A17 stores `19000/2026306` in both version/date pairs. The old mate-group clock coexists with the nonzero version mark, while the principal planes and origin retain zero last-update fields in the same file. None of these archive values supplies a builder default. [Disclosed source lock](../v2026/heldout/AssemblyPlanarMateSourceLock01.json)

Registration and the two exact post-registration operations give a constructor-backed recipe for an explicitly modeled phase. Full dynamic path attribution to A17, the runtime endpoint predicate results on generated graphs, and the final ordering of all version and clock updates remain open. No held-out files or native application runs were used. Generated bytes still require the applicable native load, rebuild, save and reopen checks. [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
