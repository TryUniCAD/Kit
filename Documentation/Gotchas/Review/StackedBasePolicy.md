# Old stacked bases can lack current reviewer policy

The first hosted review of PR #330 used its old target revision to read current policy documents.
That revision did not contain `Documentation/Planning/Generated/Tasks.md`.
Input preparation failed before the model started in [run 46163285662](https://github.com/TryUniCAD/Kit/actions/runs/46163285662).

Read review policy from the trusted workflow revision.
Read proposed source from its exact head, previous source from the merge base and current target source from the live target revision.
Record those revisions separately in the review context.
Do not require an old feature branch to contain the current reviewer implementation.
