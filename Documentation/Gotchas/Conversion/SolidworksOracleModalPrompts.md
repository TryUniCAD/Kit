# SOLIDWORKS oracle modal prompts

## Expectation

A batch script can open every generated part in SOLIDWORKS with `OpenDoc`, rebuild it, and
report one line per file.

## Actual behavior

SOLIDWORKS blocks the batch on modal prompts. A part written by Kit is newer than the
vendor baseline, so the first open shows an `Older version file` dialog. A part with
external references then shows `Open External Referenced documents`. Both dialogs wait for
input, so `cscript` never returns and `prlctl exec` times out without output.

The prompts are interactive-session state, not a format failure. A single-file run through
`OracleDrive.vbs` or `OracleOpen.vbs` succeeds because the dialog is dismissed or does not
appear for that file.

## Workaround

Validate files one at a time with `OracleDrive.vbs` or `OracleOpen.vbs`, or dismiss the
prompts once in the interactive session and enable their `Don't display this dialog box
again` options before running a batch. Do not treat a batch timeout as a model rejection.

## Evidence

On 2026-11-14 a 57-file `OracleBatch.vbs` run timed out after 20 minutes with the
`Open External Referenced documents` dialog visible. The same generated
`OracleTriangle.SLDPRT`, `OracleBox.SLDPRT`, and `OracleV8Part.SLDPRT` opened and rebuilt
successfully through the single-file scripts, as recorded in
[recent oracle runs](../../../re/solidworks/records/RecentOracleRuns.md).
