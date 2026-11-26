from mcp_server.core.exceptions import AppError
from mcp_server.core.server import CREATES_CONTENT, mcp
from mcp_server.integrations.bitbucket.client import get_bitbucket_client


@mcp.tool(annotations=CREATES_CONTENT)
async def bitbucket_create_pr(
    repo_slug: str,
    title: str,
    source_branch: str,
    destination_branch: str | None = None,
    description: str = "",
    close_source_branch: bool = False,
) -> str:
    """Create a Bitbucket pull request. Show the user the full content before calling this.

    Args:
        repo_slug: The repository slug (e.g., "my-awesome-repo").
        title: The pull request title.
        source_branch: The branch containing the changes. It must already be pushed.
        destination_branch: The target branch. Defaults to the repository's main branch.
        description: The pull request description, in Markdown.
        close_source_branch: Whether to delete the source branch after merging.

    Returns:
        A confirmation with the new pull request's ID and URL.
    """
    try:
        client = get_bitbucket_client()
        pr = await client.create_pull_request(
            repo_slug,
            title,
            source_branch,
            destination_branch,
            description,
            close_source_branch,
        )
        return f"Created PR #{pr.id}: {pr.title}\n{pr.html_url}"
    except AppError as e:
        return (
            f"Error: Could not create the pull request in '{repo_slug}'. Details: {e!s}"
        )
    except Exception as e:
        return f"Unexpected error creating the pull request. It may still have been created, so check before retrying. ({e!s})"
