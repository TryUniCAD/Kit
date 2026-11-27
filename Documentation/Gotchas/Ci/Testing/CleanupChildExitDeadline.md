# Cleanup child exit deadline

The provider cleanup probe records whether an owned child survives its
parent. It checked the child once, immediately after the supervisor
returned. Windows can still report a child from a just-closed job as live
for a short time, so the parent-exit case failed without any cleanup defect.

A Windows merge-queue candidate failed `CheckCleanup[parentexit-None]` this
way. The queued change touched only the run-defaults CLI.
[Windows shard](https://github.com/TryUniCAD/Kit/actions/runs/45802932828/job/139851050744)

Poll the child for up to three seconds before recording `child_still_live`,
matching the [session descendant deadline](SessionDescendantExitDeadline.md).
A child that outlives the deadline still fails the case.
[Cleanup probe](../../../../tests/Research/Inference/BuilderDevelopment/Generation/RunCleanup.py) ·
[Cleanup cases](../../../../tests/Research/Inference/BuilderDevelopment/Generation/ProviderCleanupTests.py)
