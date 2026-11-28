# PR conversation reactions require Issues write permission

Pull requests write permission can publish a review but does not authorize reactions to its conversation comments.
GitHub classifies those comments under the issue-comment reaction API, which requires Issues write.
Add that permission to the installed app and accept the installation update before enabling reaction steps.

The starting reaction token requests only Issues write.
The completion token also requests Pull requests read to verify the terminal review and Checks write to report workflow failure.
They are separate from account authentication and publishing credentials.
See [the GitHub reaction permission contract](https://docs.github.com/en/rest/reactions/reactions#create-reaction-for-an-issue-comment).
