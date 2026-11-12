// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

async function VerifyVersionApproval(Github, Repository, Pull, Version) {
  const Command = `/approve-release-version ${Version} ${Pull.head.sha}`;
  let Cursor = null;
  do {
    const Data = await Github.graphql(
      `query($owner:String!,$name:String!,$number:Int!,$cursor:String) {
        repository(owner:$owner,name:$name) {
          pullRequest(number:$number) {
            comments(first:100,after:$cursor) {
              pageInfo { hasNextPage endCursor }
              nodes { body lastEditedAt isMinimized author { login ... on User { databaseId } } }
            }
          }
        }
      }`,
      {
        owner: Repository.owner,
        name: Repository.repo,
        number: Pull.number,
        cursor: Cursor,
      },
    );
    const Comments = Data.repository.pullRequest.comments;
    for (const Comment of Comments.nodes) {
      if (
        Comment.body.trim() !== Command ||
        Comment.lastEditedAt ||
        Comment.isMinimized ||
        !Comment.author?.databaseId
      )
        continue;
      let Role;
      try {
        Role = await Github.rest.repos.getCollaboratorPermissionLevel({
          ...Repository,
          username: Comment.author.login,
        });
      } catch (ErrorInfo) {
        if (ErrorInfo.status === 404) continue;
        throw ErrorInfo;
      }
      if (
        Role.data.permission === "admin" &&
        Role.data.user?.id === Comment.author.databaseId
      )
        return;
    }
    Cursor = Comments.pageInfo.hasNextPage ? Comments.pageInfo.endCursor : null;
  } while (Cursor);
  throw new Error(
    `A repository administrator must post "${Command}" on PR #${Pull.number}.`,
  );
}

module.exports = { VerifyVersionApproval };
