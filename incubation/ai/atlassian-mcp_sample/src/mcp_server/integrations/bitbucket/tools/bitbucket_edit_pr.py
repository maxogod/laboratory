from mcp_server.core.exceptions import AppError
from mcp_server.core.server import OVERWRITES_CONTENT, mcp
from mcp_server.integrations.bitbucket.client import get_bitbucket_client


@mcp.tool(annotations=OVERWRITES_CONTENT)
async def bitbucket_edit_pr(
    repo_slug: str,
    pull_request_id: int,
    title: str | None = None,
    description: str | None = None,
) -> str:
    """Overwrite the title and/or description of a Bitbucket pull request.

    Previous values are lost, so read the pull request first and show the user the
    current and new content before calling this. At least one field must be given.

    Args:
        repo_slug: The repository slug (e.g., "my-awesome-repo").
        pull_request_id: The ID of the pull request.
        title: The new title. Omit to keep the current one.
        description: The complete new description, in Markdown. Omit to keep the current one.

    Returns:
        A confirmation with the pull request's URL.
    """
    if title is None and description is None:
        return "Error: At least one field ('title' or 'description') must be specified."

    try:
        client = get_bitbucket_client()
        pr = await client.update_pull_request(
            repo_slug, pull_request_id, title, description
        )
        return f"Updated PR #{pr.id}: {pr.title}\n{pr.html_url}"
    except AppError as e:
        return f"Error: Could not update pull request #{pull_request_id} in '{repo_slug}'. Details: {e!s}"
    except Exception as e:
        return f"Unexpected error updating pull request #{pull_request_id}. It may still have been updated, so check before retrying. ({e!s})"
