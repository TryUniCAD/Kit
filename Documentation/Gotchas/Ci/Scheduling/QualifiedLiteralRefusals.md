# Refusal fixtures can conflict with a newly qualified grammar

The signed-prism harness expected `-10 mm` to fail strict reading.
PR 278 independently qualified that plain negative literal with saved native controls and measurement receipts.
Its combined queue candidate therefore failed the old refusal assertion even though the new behavior matched its stated contract.
See the [failed candidate job](https://github.com/TryUniCAD/Kit/actions/runs/45387011710/job/138421137066).

Keep strict refusal coverage on an expression outside both qualified grammars.
The harness uses an arithmetic formula and checks the exact diagnostic for the two supported reader revisions.
Do not suppress rejection checks or restore the obsolete literal restriction.
