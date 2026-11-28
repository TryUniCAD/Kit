# PR conversation reactions can require both write permissions

GitHub documents Issues write for the issue-comment reaction API.
The installed app nevertheless received HTTP 403 when reacting to the PR #398 conversation with Issues write alone.
Issues write plus Pull requests read also received HTTP 403.
The same operation with Issues write and Pull requests write returned HTTP 201 and the registered bot identity.
All diagnostic tokens were restricted to Kit and revoked after the probe.

Request both write scopes on starting and completion reaction tokens.
The installation already needs both for its review and reaction responsibilities.
The completion token also requests Checks write to report workflow failure.
They are separate from account authentication and publishing credentials.
See [the GitHub reaction permission contract](https://docs.github.com/en/rest/reactions/reactions#create-reaction-for-an-issue-comment).
