# Workflow completion triggers

A `workflow_run` cleanup might appear safe when it checks out only the default-branch SHA and never consumes candidate artifacts.
The repository's pedantic security audit rejects that trigger regardless of those constraints.
The first [cleanup PR audit](https://github.com/TryUniCAD/Kit/actions/runs/45084871376/job/137401204600) reported `dangerous-triggers` for it.

Use queue-branch deletion events and trusted `main` updates for this operational cleanup instead.
Keep the audit enabled without adding a suppression.
Both events use trusted main/default-branch code and avoid executing candidate code with cancellation privileges.
Verify actual event delivery and runner release after the workflow reaches the default branch.
