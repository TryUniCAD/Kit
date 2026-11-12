// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

const { IsRepoAdmin } = require("./IsRepoAdmin.cjs");

async function CheckApproval(Github, Repository, PullRequest, Version) {
  const Command = `/approve-release-version ${Version} ${PullRequest.head.sha}`;
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
        number: PullRequest.number,
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
      if (await IsRepoAdmin(Github, Repository, Comment.author)) return;
    }
    Cursor = Comments.pageInfo.hasNextPage ? Comments.pageInfo.endCursor : null;
  } while (Cursor);
  throw new Error(
    `A repository administrator must post "${Command}" on PR #${PullRequest.number}.`,
  );
}

module.exports = { CheckApproval };
