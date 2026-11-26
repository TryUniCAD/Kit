# Private email can reject research pushes

## Expectation

An authenticated account with repository write permission can appear ready to publish a locally created commit.

## Observed behavior

The first branch push for research PR #263 was rejected with GitHub error `GH007`.
The commit author email was protected by the account privacy settings.
No branch was published by that rejected push.

## Workaround

Read the authenticated account identity and use its verified GitHub noreply address for task-owned commits.
For an unpublished task-owned commit, correct its author metadata before retrying publication.
Do not change account privacy protections or rewrite unrelated commits.
The corrected research branch was accepted by GitHub.
