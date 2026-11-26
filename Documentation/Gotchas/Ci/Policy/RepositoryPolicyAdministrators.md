# Repository-policy authority and GitHub roles differ

## Expectation

A repository-policy administrator might be expected to have GitHub's `admin` role.

## Observed behavior

The user designated `jdharcourt` as a repository-policy administrator with merge privileges.
On 2026-11-26, `GET /repos/TryUniCAD/Kit/collaborators/jdharcourt/permission` returned `write` and `admin: false`.
The designation does not establish GitHub platform admin access.

## Required handling

Verify the requester's identity against the [repository administrator policy](../../../../.agents/skills/standard-pr-practice/SKILL.md#administrator-requested-merges).
Keep platform capability, explicit merge authorization, and passing readiness gates separate.
Do not bypass enforced protections or claim that documentation changes GitHub permissions.
