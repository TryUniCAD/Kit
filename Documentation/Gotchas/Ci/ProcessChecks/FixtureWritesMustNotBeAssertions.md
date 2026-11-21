# Fixture writes must run outside assertions

## Expectation

An assertion comparing `OutputFile.write(payload)` with the expected length
always creates the intended negative fixture before invoking its process.

## Actual behavior

Optimized Python can remove the entire assertion expression. A file opened with
exclusive creation can therefore remain empty when its write appears only inside
an assertion. The curve inventory's intended 64-byte truncated input had this
side effect in its preparation helper; static review identified the issue.
The shared curve receipt helper also placed stdout, stderr and scope-file writes
inside assertions, exposing its evidence retention to the same omission.

## Workaround

Execute the write as a normal statement, retain its returned byte count, and
assert only that the count has the expected value. Keep fixture membership,
hash and failure-result checks in the real process suite. No optimized process
execution is required or claimed by this source correction.

The [specific repair](../../../Changes/Solidworks/Model/SolidworksFixturePreparationWrites.md)
preserves the existing source input, 64-byte truncation and negative CLI case.
