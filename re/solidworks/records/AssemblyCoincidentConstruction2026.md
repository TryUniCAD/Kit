# Generated coincident planar mate

The version-19000 research assembly composer constructs one aligned
coincident mate between two principal planes on separate occurrences of
one generated rectangular child. The caller supplies the two ordered
selections and the independently fixed occurrence. The model attaches
the mate to its actual group and generates both the resolved and detached
wrapper graphs from the child and parent.
[Native registration rules](CoincidentMatePublication2026.md),
[update lifecycle](CoincidentMateLifecycle2026.md),
and [wrapper construction](AssemblyPlanarEndpointConstruction2026.md).

| Owner | Generated state |
| --- | --- |
| Mate object | `moMateCoincident` owns the two resolved wrappers and the two detached rows keyed by endpoint order. The explicit alignment is 1. The initial solver state `f3b8` is 0. The feature starts with the constructor's pending-update word and zero last-update version words. |
| Occurrences | The authored anchor has `f408=1`. Both occurrences start at solve status `f400=3`. The original placements and child configuration are shared with the endpoint graphs. |
| Config-0 | The two ordered resolved wrappers acquire reference IDs 0 and 1 using the shared assembly counter. The next reference ID is 2. The occurrences and their external-feature aliases retain their original owners. |
| ResolvedFeatures and MatesList | The resolved stream includes the previously constructed mate group with empty wire children. The mate list stores the one mate using the first free archive slot of the resolved stream. |
| Header2 and Config-0-ModelHeader | The mate's allocated persistent ID and authored name identify a creation log in both headers. The construction samples the authored UTC creation time at whole-second precision for the corresponding feature FILETIME. Both headers advance the next persistent ID and keep the derived occurrence count at two. |
| Configuration manager | Active configuration progress follows the mate allocation. Its epoch and occurrence count retain their independent rules. |

The ordinary A17 control publishes the mate group in KeyWords and keeps
the individual coincident mate in the native mate list. The generated
XML uses the same group ownership when the existing XML indexes are enabled.

## Guarded construction

`CoincidentMateBundleProcess.py` accepts one JSON object with `bundle`
and the optional `include_xml_metadata` setting. Use the ordinary
assembly and child requests and provide two occurrences. Add one mate
in `bundle.mates` with `kind` set to `coincident`, `alignment` set to
`aligned`, a name, a zero-based `fixed_occurrence`, and two
`endpoints` with `occurrence` and `datum` keys. Optional `created_at`
provides the sampled Unix-seconds value. The assembly modification time
is its deterministic default.

```sh
python3.14 -I -B re/tooling/sw2026/CoincidentMateBundleProcess.py < /private/coincident-request.json
```

The process returns generated parent and child artifacts, result hashes,
and typed stream comparisons. It executes before any native application
runs and records the file-read guard.

| Authored request | Geometry and selection | Result |
| --- | --- | --- |
| AlignedPlatePair | 31.7 × 12.6 × 8.9 mm child. The first occurrence is fixed at the origin and the second translates by (107.4, 0, 12.3) mm. Both use the Top Plane and identity rotation. | 2,776 mate-list bytes and map counts 76 → 133 → 161. Both headers log mate ID 19 at the authored time. |
| RotatedDatumPair | 24.2 × 18.3 × 6.8 mm child. The second occurrence is fixed, translates by (139.1, 0, −17.7) mm and rotates by 0.73 rad about the Top Plane normal. The two selections are reversed. | 2,946 mate-list bytes with the distinct world frame, same independent allocation rules and application-specific ownership. |

Both cases reproduce all six changed or referenced logical streams and
complete the mate-list read and write using qualified class schemas.
The guarded builder performs zero runtime file reads. The process rejects
an unqualified alignment, repeated occurrence and missing datum.
The first generated pair opened cleanly in SOLIDWORKS, retained the ordered
plane references through a driving child depth edit, and saved and reopened
with the new geometry. Both controls passed. Its input placements were
already coincident. Placement correction and held-out acceptance remain open.
[Construction receipt](../measurements/2026/GeneratedCoincidentMateBundle01.json) ·
[Native trial](GeneratedCoincidentMateTrial2026.md)
