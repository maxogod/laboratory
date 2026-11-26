import asyncio

from mcp_server.core.exceptions import AppError
from mcp_server.core.server import READ_ONLY, mcp
from mcp_server.integrations.bitbucket.client import get_bitbucket_client
from mcp_server.integrations.bitbucket.models import BitbucketComment, BitbucketCommit


def _format_commit(commit: BitbucketCommit) -> str:
    author = commit.author.user.display_name if commit.author.user else None
    return (
        f"- {commit.hash[:7]} by {author or commit.author.raw} "
        f"on {commit.date.strftime('%Y-%m-%d')}: {commit.message.strip()}"
    )


def _format_comment(comment: BitbucketComment) -> str:
    return (
        f"- {comment.user.display_name} "
        f"({comment.created_on.strftime('%Y-%m-%d %H:%M')}):\n"
        f"  {comment.content.raw}"
    )


@mcp.tool(annotations=READ_ONLY)
async def bitbucket_read_pr(repo_slug: str, pull_request_id: int) -> str:
    """Read a Bitbucket pull request: its metadata, description, commits and comments.

    Args:
        repo_slug: The repository slug (e.g., "my-awesome-repo").
        pull_request_id: The ID of the pull request.

    Returns:
        A formatted string containing the pull request details, commits and comments.
    """
    try:
        client = get_bitbucket_client()
        pr, commits, comments = await asyncio.gather(
            client.get_pull_request(repo_slug, pull_request_id),
            client.get_pull_request_commits(repo_slug, pull_request_id),
            client.get_pull_request_comments(repo_slug, pull_request_id),
        )

        sorted_comments = sorted(comments, key=lambda c: c.created_on)
        return "\n".join(
            [
                f"PR #{pr.id}: {pr.title} (State: {pr.state})",
                f"Author: {pr.author.display_name}",
                f"Created: {pr.created_on.strftime('%Y-%m-%d %H:%M')}",
                f"Updated: {pr.updated_on.strftime('%Y-%m-%d %H:%M')}",
                "---",
                "Description:",
                pr.description or "No description provided.",
                "---",
                f"Commits ({len(commits)}):",
                *([_format_commit(c) for c in commits] or ["No commits found."]),
                "---",
                f"Comments ({len(comments)}):",
                *(
                    [_format_comment(c) for c in sorted_comments]
                    or ["No comments found."]
                ),
            ]
        )
    except AppError as e:
        return f"Error: Could not read pull request #{pull_request_id} from '{repo_slug}'. It may not exist, you lack permissions, or the integration is unconfigured. Details: {e!s}"
    except Exception as e:
        return f"Unexpected error reading pull request. Please try again. ({e!s})"
