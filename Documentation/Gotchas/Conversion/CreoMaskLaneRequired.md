# Creo AllFeatur masks need a non-empty lane and nothing else

## Expectation

`AllFeatur`'s `cr_flags_xar` is a large array of signed 32-bit values (402 bytes in the first record) that
reads like dirty-state flags. The reasonable assumptions are that it carries document state, that a
generated default would be wrong, or that the loader validates it.

## Actual behaviour

It validates nothing but the shape. `re/creo/tools/SlotBisect.py` rewrites the lane in every feature
record with a generated all-clean vector through the shipped encoder, so every candidate is well formed:

| Candidate | Result |
| --- | --- |
| every slot `-1`, count 252 | loads |
| every slot `-1`, count 4 / 2 / 1 | loads |
| single slot, value `0` | loads |
| every slot `-1`, count 0 | fails |

So neither the values nor the count matter. The only rule is that the array must be non-empty, and
`Author.CleanFlagValue()` (`f1 f8 01 f6`) plus `Author.CleanFlagElements()` (`f6`) satisfy it: a control
whose four lanes are replaced by exactly those loads with `End` and `MT Part Solid`, `AllFeatur`
`3478` → `1895` bytes.

The field itself is still required: `re/creo/tools/OmitMask.py` removes it from all four records and the
process exits.

## Workaround

Do not spend effort modelling the mask. Emit one clean slot.

## The trap that cost the most time

Creo launched as `parametric.exe -g:no_graphics <file>` sometimes exits with **no `End` line and no
`dbg_err_crash`**. That is indistinguishable from a hard rejection, and it produced two false
measurements here: "every value `-1` fails" and "every value `0` fails" were both flaky launches, and the
all-clean candidate loaded on retry.

Treat a launch with no `End` and no error line as *inconclusive*, not as a failure, and re-run it before
recording anything. Failure verdicts should be carried by an explicit message (`cannot be retrieved`,
`not a valid PART file`, `dbg_err_crash`) or by two independent silent exits.

## Evidence

- `re/creo/tools/SlotBisect.py` — rewrites the lane with generated vectors; `all`, `len:N` and slot
  literal modes.
- `re/creo/tools/OmitMask.py` — removes the field entirely.
- `re/creo/data-model/FeatureRecord.md` — encoder table, bisection table, retractions.
- `Documentation/Changes/Creo/CreoGenerativeAuthor.md` — launch logs.
