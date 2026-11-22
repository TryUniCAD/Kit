# Convert measured SOLIDWORKS sweeps to neutral JSON

`kit convert INPUT.SLDPRT OUTPUT.json --to interchange.json` preserves
the typed section, path, both D1 drivers and analytic solid of a
canonical cold Standard sweep. The command independently rebuilds the
portable projection and checks the complete canonical source identity
before the JSON writer runs.

Both measured inputs passed the real conversion command and reopened
as equal portable documents. Other CAD export targets retain their
own capability gates. Native SOLIDWORKS publication still requires
the exact matching measurement receipt.

[Scoped command and configuration evidence](../../../../../re/solidworks/records/ScopedSweepReadback2026.md)
