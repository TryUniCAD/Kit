# Verify native lifecycle of a preserved blank drawing rewrite

The SOLIDWORKS 2026 research observer verifies a preserved blank drawing after
the normal SDK reads the original and generates a new archive with an explicit
self-file locator and save event. The job requires the exact two guarded
candidates, their source-owner evidence and a pristine blank control.

Run `InspectBlankRewrite.py verify JOB --sha256 HASH` and then the corresponding
`run` command under the reserved oracle. Each lane checks the sheet, scale,
ordered tree, rebuild and native edit before saving a separate copy. A new
process verifies that copy. The native receipt records the complete bracket.
