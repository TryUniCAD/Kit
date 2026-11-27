# Relative Python paths change with the child directory

## Expectation

A CLI integration process should import the SDK from the checkout under test.

## Actual behavior

The shared `CliProcess` helper launches its child in the test's temporary directory.
A relative `PYTHONPATH=src:Cli` then resolves beneath that directory.
The child can import an older installed SDK instead of the changed checkout.
Three reverse-preparation CLI checks initially reported the old forward-only guard for this reason.

## Workaround

Set `PYTHONPATH` to the absolute checkout `src` and `Cli` directories for the scoped child process.
Use `os.pathsep` for the platform separator and restore the environment through the existing pytest fixture.
Do not change the shared helper or weaken the expected production failure.

The corrected processes reach the unchanged exact native measurement gate.
[Retained attempts](../../../../re/solidworks/DecodedPromotion20261127/Preparation/Receipt.json) distinguish this harness failure from a native CAD result.
