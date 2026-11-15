# Fusion drawing acceptance record

## Problem

The Fusion drawing work had evidence spread across change entries, gotchas and research reports.
No single page said which of the [CAD success criteria](../../../Reference/Operations/CadSuccessCriteria.md)
pass, which fail, and why, so a reader could not tell a measured result from a claim.

## Change

[`Documentation/Reference/Operations/FusionDrawingAcceptance.md`](../../../Reference/Operations/FusionDrawingAcceptance.md)
records the verdict per criterion with the measured numbers.

| Criterion                  | Verdict                                              |
| -------------------------- | ---------------------------------------------------- |
| C1 no donor data           | pass, scanner clean and no CAD files under `src/`    |
| C2 no CAD runtime          | pass, Fusion is the oracle only                      |
| C3 lossless                | pass, 60 of 60 DWG and 248 of 248 F2D byte-exact     |
| C4 fully parametric        | pass for designs, pass for drawing properties        |
| C5 to C7 loadable and usable | **fail** for a drawing authored from nothing       |
| C8 honest attestation      | the failure is stated as a failure                   |
| C9 complete implementation | incomplete, blocked by policy                        |
| C10 generalization         | held-out design case and one-input drawing controls  |
| C11 traceable knowledge    | five gotchas linked                                  |

## Behavior

No code changes. The page is a record, and it links the gotchas that carry each finding.

## Verification

Every number on the page comes from a run recorded in this repository or in the research workspace:

| Number                          | Source                                        |
| ------------------------------- | --------------------------------------------- |
| 60 of 60 DWG, 248 of 248 F2D    | corpus round-trip run on this branch          |
| 60 of 60 headers typed          | same run                                      |
| 3078 files scanned              | `tools.Donors.CheckReplays src`               |
| design volumes                  | `OpenDesign.py` reports in the research tree  |
| sheet, scale and position       | `BisectRound.py` reports for the three cases  |

## Limits

The page states a failure. It does not make the drawing writer loadable, and it does not claim the
objective is met.
