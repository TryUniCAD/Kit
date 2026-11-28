# Organization owners cannot override enterprise Actions approval policy

An organization owner might expect to enable Actions approvals in organization settings.
The API rejected that change with HTTP 409 for TryUniCAD during this setup.
The response stated: `The enterprise does not allow GitHub Actions to approve pull requests`.

The disabled setting governs the built-in `GITHUB_TOKEN`.
A separately authorized GitHub App uses its own installation token and permissions.
An app must still follow applicable organization and enterprise policy.
See [GitHub's repository settings reference](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository).
