# Reviewer app branding

The owner updated the organization review app name and logo in GitHub settings.
The reviewer registry now uses the verified renamed app slug and bot login.
App and bot numeric identities remain unchanged, preserving the installed app and its credentials.

`python .github/scripts/Review/Configure.py APP_SLUG` verifies the live app, owner, bot, installation, and required permissions.
It updates both reviewer identity and mention commands from that verified slug.
Read the current commands in `AccountReview.MentionCommands` in the reviewer registry.

Verification read back the public app and bot records, selected-repository installation, and unchanged permissions.
The downloaded public bot avatar was visually checked against the organization logo.
Live mention execution and review approval still require default-branch deployment and activation.
