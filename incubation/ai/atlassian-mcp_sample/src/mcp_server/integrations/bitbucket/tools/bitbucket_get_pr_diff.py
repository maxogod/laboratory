from mcp_server.core.exceptions import AppError
from mcp_server.core.server import READ_ONLY, mcp
from mcp_server.integrations.bitbucket.client import get_bitbucket_client


@mcp.tool(annotations=READ_ONLY)
async def bitbucket_get_pr_diff(repo_slug: str, pull_request_id: int) -> str:
    """Get the diff of a Bitbucket pull request.

    Args:
        repo_slug: The repository slug (e.g., "my-awesome-repo").
        pull_request_id: The ID of the pull request.

    Returns:
        The diff of the pull request.
    """
    try:
        client = get_bitbucket_client()
        return await client.get_pull_request_diff(repo_slug, pull_request_id)
    except AppError as e:
        return f"Error: Could not get diff for pull request #{pull_request_id} from '{repo_slug}'. It may not exist, you lack permissions, or the integration is unconfigured. Details: {e!s}"
    except Exception as e:
        return f"Unexpected error getting pull request diff. Please try again. ({e!s})"
