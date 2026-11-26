# Shared register insertions in a merge queue

A PR can be conflict-free against main but unable to join a queue candidate that includes an earlier PR.

PR 274 and the preceding PR 272 both inserted a different task immediately after the same heading in `AutomationSteps.md`. GitHub kept PR 274 in the queue as `UNMERGEABLE` with no candidate commit. There was no failing PR 274 test run. A local `git merge-tree --write-tree` against preceding candidate `399ae429476823e97ba631cc7859825c728f7cd3` reproduced the shared-register conflict; the same check against main was clean.

Move the task-owned entry to a separate stable location while preserving its heading anchor and every other owner's entry. Validate the combined tree against the observed preceding candidate before requeueing. Do not import an unmerged predecessor's implementation into the task branch or weaken queue acceptance to solve a documentation conflict.
