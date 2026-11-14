# SOLIDWORKS recorded payload ratchet

## Change

The supported SOLIDWORKS families were described as constructive with zero opaque bytes.
Each family under `src/convert/adapters/solidworks/programs/` is a recorded payload.
A recorded payload is one vendor-saved stream, re-encoded as typed field operations.
Each operation stores an absolute offset, a width, an owner, a kind, and the value from that save.
The writer re-emits the list at the saved length and overrides selected offsets.
This form cannot change object count or topology, so each new profile needed another recorded program.

This change records that state and stops the debt from growing:

- `tools/Donors/CheckReplays.py` counts recorded field operations and recorded payload re-emission calls in production code.
- `tools/Donors/ReplayBaseline.txt` holds the permitted count for each program root.
- The `Python steering` workflow runs the check on `src` for pull requests, merge groups, and `main`.
- [AGENTS.md](../../../AGENTS.md) and the preamble of the [no donor blocks standard](../../../.agents/skills/standard-pr-practice/references/Standards/Portable/NoDonorBlocks.md) state the current SOLIDWORKS state and the required generative direction.
- The [SOLIDWORKS adapter guide](../../Reference/Adapters/Solidworks.md), `re/README.md`, `re/solidworks/README.md`, and `re/solidworks/CorpusCoverage.md` no longer describe the programs as constructive.
- The [term register](../../Standards/Terminology.md) defines a recorded payload.

## Behavior

A recorded field operation is a tuple literal that starts with two integer literals and has a lowercase kind string, such as `primitive:double` or `classref`, as its fourth item.
A recorded payload re-emission call is a call to `ReplayResolved`, `ReplayFixed`, `ReplayAssembly`, or `ReplayConfig`.
The check groups counts by program root.
The root is the directory above a `Methods` or `Owners` directory, or else the directory of the file.

| Result                                             | Exit status | Baseline change                        |
| -------------------------------------------------- | ----------: | -------------------------------------- |
| Every count equals its baseline entry              |           0 | None                                   |
| A root or rule is new, or a count grew             |           1 | Refused, also with `--update-baseline` |
| A count fell or a root is gone                     |           1 | Lowered with `--update-baseline`       |
| A path is missing or the baseline cannot be parsed |           2 | None                                   |

The check compares a baseline entry for a fall only when the entry's root is inside a scanned directory.
An update keeps every other entry unchanged.
A scan of single files or of a directory below a root therefore cannot lower or remove that root's entry.
The check resolves each path, so the same file given twice is counted once.
An unknown rule code in the baseline is an input error.

At introduction the check found 185,090 recorded field operations and 43 re-emission calls in 43 program roots.

## Usage

Run the check from the repository root:

```sh
uv run python -m tools.Donors.CheckReplays --baseline-file tools/Donors/ReplayBaseline.txt src
```

After you delete or generate part of a recorded program, lower the baseline and commit it:

```sh
uv run python -m tools.Donors.CheckReplays --baseline-file tools/Donors/ReplayBaseline.txt --update-baseline src
```

Do not edit the baseline to add a root or raise a count.

## Limits

The check detects the field-operation tuple form used by the SOLIDWORKS programs.
It does not detect recorded bytes in other forms, such as encoded blobs or captured tables in other adapters.
Review and the no donor blocks standard still apply to those forms.
The check does not remove existing debt.
The generative serializer that replaces the programs is separate work.

## Verification

The check passed on `src` against the committed baseline.
Its per-root counts match the documented programs: 3,522 operations for the box `ResolvedFeatures` program and 4,345 for the box `Config-0` program.
No root outside `src/convert/adapters/solidworks/programs/` matched.
Black, Ruff, mypy, pyright, repository-wide steering, zizmor, and Prettier passed locally.
`tests/steering/ReplayRatchetTests.py` runs the command as a subprocess for equal, grown, new, fallen, and invalid inputs.
Those tests were not run locally under the repository test policy.
PR CI runs them.

## Related information

- [Zero opaque bytes is not generation](../../Gotchas/Conversion/ZeroOpaqueBytesNotGenerated.md)
- [No donor blocks standard](../../../.agents/skills/standard-pr-practice/references/Standards/Portable/NoDonorBlocks.md)
- `re/solidworks/archive/Grammar.md` section 6, derived caches
