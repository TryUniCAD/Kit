# Queue entry identity

A queued pull request can receive a replacement candidate without leaving the queue.
Checking only whether `mergeQueueEntry` exists therefore preserves its obsolete candidate's run.
This keeps abandoned jobs competing with the replacement.
The [cleanup review](https://github.com/TryUniCAD/Kit/pull/268#discussion_r4660645751) identified that gap.

Compare the current entry's `headCommit.oid` with the run SHA, in addition to the exact missing-branch check and the complete queue-head snapshot.
Preserve matching heads and unavailable candidate identities.
A valid different head identifies a replacement and allows cancellation of the old branchless run.
The [GraphQL reference](https://docs.github.com/en/graphql/reference/pulls#mergequeueentry) defines the entry's head commit separately from its pull request.
The process fixture includes both candidate runs, a deleted old ref, and the replacement head in the active snapshot.
Actual runner release remains subject to post-rollout verification.
