# Principal-plane revolve held-out evaluation

Task `B04-SW2026-REVOLVE-PRINCIPAL` advances the internal ordinary
rectangular boss through the actual selected Top and Right support.
The original source lock puts both native saves, their authoring
intent and two receipt hashes per case before the first orientation
writer at `2e9d58ae807c86f93f87f7362e4be1ca32d0aa34`. The same
source tree `c1967f83c511b6ffc699684335e132704851a1fb` produced
the four disclosed native lifecycles and is the held-out writer.
[Source lock](../v2026/heldout/PrincipalRevolveSourceLock01.json) · [Disclosed lifecycle](../measurements/2026/SdkPrincipalRevolveNative01.json)

## Freeze and custody

Commit the protocol and evaluator before opening either sealed
original or its measurements. The host freeze verifies Git
ancestry, the exact source tree, the source lock chronology, the
four disclosed outcomes and the healthy control file. It emits
`Freeze.json`, a packet with the disclosed revision's production
Git archive and exact research blobs, and the matching evaluator
on the Mac share. Record the freeze digest before issuing either
guest command. The first bundle used the release archive's
`export-ignore` and omitted the research inventory. Its validation
stopped before the specification or either native original was read.
The second bundle adds the individually pinned research blobs.
[Frozen evaluator](../../tooling/sw2026/revolve/PrincipalWriter/EvaluatePrincipalRevolves.py) · [Source staging gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/SourceStaging/FrozenSourceNeedsCanonicalPaths.md)

The Windows preparation opens the hash-pinned private authored
specification after validation of the frozen files. It selects the
two individually named Top and Right cases and passes their
neutral geometry, dimensions, selections and edit angles to a
fresh SDK-only worker as structured values. Each invocation runs
`PrepareRevolve` through both a path and a named stream. The
isolated worker refuses file or native application access during
construction. Its strict read verifies the closed solid and actual
datum, axis and D1 owners. All ten measured streams must replay.
Both candidate hashes and numeric predictions enter
`Generation.json` before reference files or phase records open.

## Windows read guard recovery

The first native attempt's two controls passed. Neither candidate
launched because the strict reader's known grammar read reached
the absent Windows CPython constant `os.O_ACCMODE`. The retained
failure receipt contains no candidate observation. The portable
mask keeps the same read-only path allowance. The recovery packet
verifies that exact failure and uses the original generation
receipt, candidate files and self paths. It starts no generation
work and leaves the production SDK tree, comparisons and
thresholds pinned as before.
[Observed guard failure](../measurements/2026/PrincipalRevolveObserverGuardFailure01.json) · [Portable access mask](../../../Documentation/Gotchas/Conversion/Registry/WindowsAuditsNeedPortableAccessMask.md)

## Native comparison

The two candidates and two original native parts retain their
exact hashes. Open both kinds read-only, edit the actual D1 and
save edited derivatives to separate owned paths and reopen each
in a fresh process. Compare each candidate phase to the paired
original phase and to independent analytic predictions. The
original first two observations also match their pre-writer
receipts. Use two healthy controls with ten distinct process
births, SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`, and COM
`SldWorks.Application.34`.

For each file require one solid before and after explicit rebuild,
zero opening, feature and save warnings or errors, the same
25-row recursive feature inventory and the actual four contour
relations and selected line. Compare every contour endpoint,
the origin and three basis directions, and the actual COM body
label at every phase. Match the strict SDK label to COM on
archives with a native saved body cache. The cold SDK projection
records its placeholder label separately. Verify the unchanged signed sweep
after the edit and the edited value after a fresh reopen. Match
volume, area, mass and all three centre components to six
significant figures between paired sources and generated files,
using a `10^-12 m` zero threshold only on centre components.
Analytic positive properties use relative tolerance `2e-7`;
analytic centre components also allow `10^-10 m` absolute.
[Signed analytic formula](OrdinaryRevolveHeldoutProtocol2026.md#frame-and-signed-predictions)

Continue the post-batch control after any failed candidate. Keep
the raw native failure and observation receipts in the isolated
guest. Publish hashes, precise measurement results, and the
scope examined. The input is authored neutral intent. Full
preservation of all original native document domains has its own
exit. Public writer registration and FCStd corpus credit also
have separate exits.

## Invocation

Use the exact executable and Mac-share paths from the frozen
launch record. The second guest phase takes the exact generation
digest returned by the first.

```sh
python3.14 -B re/tooling/sw2026/revolve/PrincipalWriter/EvaluatePrincipalRevolves.py \
  freeze --name PrincipalRevolveEvaluation02
prlctl exec 'Windows 11' --current-user "$guest_python" -B "$guest_evaluator" \
  prepare --packet "$guest_freeze" --freeze-sha256 "$freeze_sha256"
prlctl exec 'Windows 11' --current-user "$guest_python" -B "$guest_evaluator" \
  native --packet "$guest_freeze" --freeze-sha256 "$freeze_sha256" \
  --generation-sha256 "$generation_sha256"
```
