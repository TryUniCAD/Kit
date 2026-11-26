# Restore Python checks on the catalogue branch

The catalogue branch predates the requirement to run Python steering, Pyright and Mypy on pull requests and merge-group candidates. The current CI aggregate rejected the three skipped jobs. This change uses the [existing job conditions](https://github.com/TryUniCAD/Kit/pull/224/files) for the dependent branch and keeps its jobs, runner definitions and allowlist.

The full checks enabled on the exact base exposed inherited diagnostics in catalogue, Windows dispatch, archive and Fusion paths. The recovery preserves the catalogue and Windows test cases, their control inputs, and their assertions. The Fusion state encoder retains its cached field order and the full baseline serialized fields. The SOLIDWORKS circle proof keeps its command-line input and output paths.

## Verification

The catalogue base is `e2fba13c8fa04ea43dcd27c02794d60a30ede151`. The dependent branch's initial restored jobs measured 57 inherited steering findings, 93 inherited Mypy errors and 196 inherited Pyright errors. That branch fixed its separate one Mypy and four Pyright findings in [PR #314](https://github.com/TryUniCAD/Kit/pull/314). See [the owning register](../../../Reference/Research/AutomationSteps.md#a08-base-python-verification-recovery).

The phase map lists all three Python checks in both phases. The aggregate excludes only jobs unique to the other phase from its required result. The existing process cases exercise skipped required Python checks and legitimately deferred research compatibility.

Windows Python 3.14.6 collected 30 existing archive, controller and format cases in the focused subset. Sixteen selected integrations passed in 45.36 seconds. The distinct saved Fusion cuboid and rectangle produced byte-identical state output before and after the typing repair, with SHA-256 `94044a721d407c9250545e753a10c852dfe4dae184ee4c34a9886f8f00fcf039` and `78e6b9b4b1619a78b4cafa9a528d6db62dcec0e2de52c52870c48c834fff68b5`. All 27 existing aggregate policy cases passed in 3.43 seconds, including the four duplicated-phase and unique-phase skip controls.
