# Principal-plane ordinary revolve reader

Task `B04-SW2026-REVOLVE-PRINCIPAL` in PR #121. This reader change starts
at `03e2e5ed376229565c6d381b132dd1c946d89218`. It extends the existing
version-19000 ordinary rectangular boss reader to the canonical Top and
Right support frames. The exact native build is SOLIDWORKS 2026 SP05.2
`34.5.2.0604`. [Source custody](PrincipalRevolveSources2026.md)

## Frame and geometry rules

`ReadRevFrame` uses the shared `ReadPrismFrame` to resolve the actual local
component, datum reference, stored axis code and profile inverse. Positive
Top and Right normals require the complete canonical tangents from
`ReadPrincAxis`. The Front admission and report scope are unchanged.
The public projection also verifies that the sketch links to the same
datum ID and exact frame before it publishes the Top or Right result.

| Plane | Local U | Local V and raw upward axis | Normal | Forward sweep tangent |
| --- | --- | --- | --- | --- |
| Front | +X | +Y | +Z | −Z |
| Top | +X | −Z | +Y | −Y |
| Right | −Z | +Y | +X | −X |

Sketch points and relations remain in local U/V. The selected line's
ordered endpoints become world points through the actual support frame.
The angular feature retains its owned positive `D1` in radians. Reversal
negates the effective world axis and leaves the selected construction line
unchanged. The cold builder continues to pass the world axis and local U
direction to the shared sweep and metric functions. The native-saved
reader still checks the actual active partition and rollback history
before binding the implicit body name.

## Guarded evidence

The [14-process receipt](../measurements/2026/PrincipalRevolveRead01.json)
has SHA-256 `27eaeb083448a48be0dfbce0abccf8fbb2c20effb3ebca4373ece99e891daac2`.
It pins both method files, the four reader files and each source and
native observation. The same Front input has identical neutral document
digests in both default and semantic-only modes. The prior
[Front cold proof](../measurements/2026/SdkColdRevolveGeometry01.json)
also reproduces its exact digest, eight geometry reads and five
malformed refusals.

The two Top directions and one independently disclosed Right reverse
part project their actual `D1`, selected line and support through both
strict SDK modes. Default reads preserve the source partition and delta
hashes and bind the native name `OrdinaryBossRevolve` to the complete
closed B-rep. The Top axis endpoints are `(4, 0, 16)` and
`(4, 0, −23)` mm. The Right axis endpoints are `(0, −21.9, −9.3)`
and `(0, 20.2, −9.3)` mm. These are model coordinates. The hash-bound
native reopen receipts record a real `D1` edit in memory. This packet
supplies the original saves for SDK readback.

Four generated neutral fixtures cover Front forward, Top forward,
Top reverse and Right reverse in the default cache-free path. The
research fixture builder derives the support wrapper and profile inverse
on fresh shared archive objects. It reads no native file. Each fixture
repeats exactly and produces one six-face solid with independently
predicted area, volume and signed section bounds. Two same-normal
quarter-turn in-plane rotations are refused by the typed and public
readers. Three forged public support identities are also refused.

The fixture construction and cold reads use no runtime files.
Native-saved and semantic-only reads use only the recorded SDK
`Config/RootLayout.json` grammar during their guarded execution.
The first run stopped on a lazy SDK validation import. The second
reached the cold worker and found that a fresh part allocates its own
plane ID. The completed method initializes validation before its
runtime guard and checks the actual authored datum ID.

```sh
python3.14 -I -B re/tooling/sw2026/revolve/PrincipalReader/AuditPrincipalReader.py \
  --sources "$disclosed_parts" --baseline-sdk "$baseline_src" \
  --right "$right_part" "$right_receipt" "$right_reopen" \
  --output "$fresh_report"
```

Supply a baseline source tree extracted from the pinned revision and
the disclosed source files and phase reports named in the receipt.
The two sealed principal-plane inputs remain sealed. This evidence
records zero new native launches, zero held-out credit and no writer
registration. [Saved and cold topology boundaries](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Revolve/SavedRevolveRowsAreNotColdMeridians.md)
