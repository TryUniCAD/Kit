# UTF-8 output needs an explicit comparison encoding

Expected: generating planning views and immediately checking them succeeds without source changes.

Observed: Windows Python 3.14 decoded text using the system encoding when `Path.read_text()` had no encoding argument.
The builder wrote UTF-8 but reported eight generated views as stale during its immediate check.
Two generation runs produced identical bytes, which ruled out ordering drift in that reproduction.

Specify `encoding="utf-8"` for maintained source reads and generated comparisons.
The process regression uses a non-ASCII task name under a legacy locale and checks its exact generated text.
See [the change and verification](../../../Changes/Planning/PlanningUtfText.md).
