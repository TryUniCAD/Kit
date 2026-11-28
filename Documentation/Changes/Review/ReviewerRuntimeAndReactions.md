# Explicit review runtime and mention reactions

Every automated, manual, and mention review uses the model and reasoning set in the reviewer registry.
The default is `gpt-6.1-terra` with `medium` reasoning.
The trusted input records these settings, the runner passes them explicitly to Codex, and the published report includes them.
Unavailable settings fail without an automatic model fallback.

The registry now matches the renamed installed app and its verified bot identity.
Read the current commands in `AccountReview.MentionCommands`.
The app requires Issues write permission for reactions to PR conversation comments.
Read-only public comment admission remains unchanged.

After preparing complete eligible input, the app adds an eyes reaction to the admitted mention.
After native publication, it replaces eyes with thumbs up for approval or thumbs down for requested changes.
A failed review or publication receives a confused reaction.
A failed runtime or publication job also creates a failed native report linked to its workflow logs, including automatic reviews without a mention.
Only the app's own progress reaction is removed; other users' reactions remain.
Full workflow cancellation or completion-job failure can prevent cleanup until a retry succeeds.
Native checks and approving reviews remain the acceptance evidence.

Live target-ref and mergeability checks now reject stale CI even when PR metadata retains an older base SHA.
PR #398 exposed this case during rollout; its existing CI evidence does not qualify the changed main revision.

The installed app rename, unchanged numeric identities, Issues write permission, and local model capability list were verified.
Formatting and source policy verification passed during implementation.
Hosted model execution, credential persistence, reaction cleanup, and native review acceptance remain pending deployment.
Review activation remains paused while this change is prepared so no new job uses the previous CLI default.
See [configuration and limits](../../Tasks/AccountReviewer.md).
