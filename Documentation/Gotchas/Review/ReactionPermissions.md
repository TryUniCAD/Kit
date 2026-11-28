# PR conversation reactions require Issues write permission

Pull requests write permission can publish a review but does not authorize reactions to its conversation comments.
GitHub classifies those comments under the issue-comment reaction API, which requires Issues write.
Add that permission to the installed app and accept the installation update before enabling reaction steps.

Reaction tokens request only Issues write, plus Pull requests read when verifying the terminal review.
They are separate from account authentication and publishing credentials.
See [the GitHub reaction permission contract](https://docs.github.com/en/rest/reactions/reactions#create-reaction-for-an-issue-comment).
