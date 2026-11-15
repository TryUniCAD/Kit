# Creo ModelCHECK does not finish unattended here

## Expectation

`modelcheck.bat` is a batch analyser shipped beside `parametric.exe`, so it looks like a way to obtain Creo-side
measurements — mass properties, feature checks — without a UI or a trail:

```text
modelcheck.bat <part.prt>
```

## Actual behaviour

It starts (`modelcheck.exe` plus `creoagent.exe` appear in the process list), it retrieves the model — the trail
it writes records `MT_CUST - Applied settings for mode # 1 : MT Part Solid`, so the part **is** loaded — and then
it never finishes. After 55 seconds there is no report in the working directory, no `std.out`, and the process is
still running; killing it leaves only `trail.txt.1`.

`modelcheck.bat` itself is a thin wrapper:

```text
"%prodir%\%MC%\obj\modelcheck.exe" %1 %2 %3 %4 %5 %6
```

and it needs `PROCESSOR_ARCHITECTURE` (or `PROCESSOR`) exported, because `prlctl exec` does not inherit it — without
that it prints `ERROR Cannot detect what machine type you have` and exits.

The shipped configuration at
`Common Files\modchk\text\usascii\config\config_init.mc` has the mode table (`# "B" = Batch`), `MODE_RUN`,
`MODE_UPDATE`, `MC_ENABLE`, `MC_METRICS` and `MC_AUTHORIZATION_FILE`, and the report/display options that would let
it terminate without a browser are what it is missing here.

## Workaround

None found. Treat ModelCHECK as unavailable as a measurement channel in this environment: the part loads under it,
which is a useful confirmation in itself, but no report is produced, so it cannot supply the body count, volume or
centre of mass that acceptance needs.

Do not conclude a part is invalid because ModelCHECK hung — it did retrieve the model first.

## Evidence

- `Documentation/Changes/Creo/CreoGenerativeAuthor.md` — the measurement gap this leaves.
- `Common Files\modchk\text\usascii\config\config_init.mc` — the mode and report options.
