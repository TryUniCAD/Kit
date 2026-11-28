# Mention triggered account review

Trusted collaborators can request a PR review with a configured app mention.
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
See [setup and mention use](../../Tasks/AccountReviewer.md).
Process admission coverage joins the existing complete test suite.
Live authorized mention execution remains pending initial workflow deployment and activation.
