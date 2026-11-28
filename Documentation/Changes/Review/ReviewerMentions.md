# Mention triggered account review

Trusted collaborators can request a PR review with a configured app mention.
The trusted scheduled workflow polls recent comments every five minutes instead of using a privileged comment-event trigger.
The exact commands live in `AccountReview.MentionCommands` in the reviewer registry.
Commands are matched against the whole comment, ignoring outer whitespace and letter case.
Quoted commands, edited comments, bot comments, and ordinary issue comments do not qualify.

A separate admission job uses read-only credentials to verify the commenter's current write, maintain, or admin permission.
Only admitted requests can start jobs that access the protected app and account credentials.
The command text never enters a shell expression or the model's prompt.

Mention selection targets the commented PR and permits explicit reassessment of the same head.
It searches the latest 100 successful aggregate CI runs and still requires current head and base evidence.
It never approves a fork or bypasses CI, review findings, score, or merge-queue gates.

Account credential jobs remain serialized; rejected public comments do not enter that credential queue.
Polling inspects the latest 100 repository comments and rotates through at most ten matching-command lookups per invocation.
The run number advances the starting position so handled comments cannot permanently starve older requests within that window.
App-attributed native report markers acknowledge each handled comment for the inspected head.
Receipt discovery reads all retained matching app checks with pagination, rather than only the latest check with the same name.
A neutral waiting-for-CI report acknowledges a request without claiming a completed review or approval.
See [setup and mention use](../../Tasks/AccountReviewer.md).
Process admission coverage joins the existing complete test suite.
Live authorized mention execution remains pending initial workflow deployment and activation.
