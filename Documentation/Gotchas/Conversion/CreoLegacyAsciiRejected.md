# Creo 2027 rejects a minimal legacy ASCII part

## Expectation

A `#UGC:2` file with a `#P_OBJECT` body and a small attribute tree is a legacy ASCII Creo part that the current application can open.

## Observed behavior

Creo 2027.2 exits when the hand-built file is opened.
The file has a valid header, `#P_OBJECT 6`, a model name, a unit name, and the `#Pro/ENGINEER` banner.
The application does not show a model window.

## Cause

The legacy ASCII form is a persistence generation, not a complete model.
The current reader requires the native model records and section set that the minimal file does not contain.
A syntactically plausible attribute tree is not a loadable part.

## Workaround

Do not use legacy ASCII as a writer target for current Creo.
Use the native PSB section model and measure the result in the target application.

## Evidence

- Hand-built file: `#UGC:2 PART 1`, `#P_OBJECT 6`, `model_name`, `principal_sys_units`, `#END_OF_P_OBJECT`, `#Pro/ENGINEER`.
- Creo 2027.2 opened the vendor empty-part control in the same session.
- The hand-built file caused the session to exit.

## Scope

This is a negative result for the legacy writer path.
It does not establish that every legacy file is invalid.
