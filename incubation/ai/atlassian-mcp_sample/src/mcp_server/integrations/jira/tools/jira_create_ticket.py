from mcp_server.core.exceptions import AppError
from mcp_server.core.server import CREATES_CONTENT, mcp
from mcp_server.integrations.jira.client import get_jira_client


@mcp.tool(annotations=CREATES_CONTENT)
async def jira_create_ticket(
    project_key: str,
    summary: str,
    issue_type: str,
    description: str | None = None,
    labels: list[str] | None = None,
) -> str:
    """Create a Jira ticket (issue). Show the user the full content before calling this.

    Args:
        project_key: The key of the project to create the ticket in (e.g., "PROJ").
        summary: The ticket title.
        issue_type: The exact issue type name used by the project (e.g., "Task", "Bug").
        description: The ticket description, in Markdown.
        labels: Labels to set on the ticket.

    Returns:
        A confirmation with the new ticket's key and URL.
    """
    try:
        client = get_jira_client()
        key = await client.create_issue(
            project_key, summary, issue_type, description, labels
        )
        return f"Created {key}: {summary}\n{client.browse_url(key)}"
    except AppError as e:
        return f"Error: Could not create the ticket in project {project_key}. Details: {e!s}"
    except Exception as e:
        return f"Unexpected error creating the ticket. It may still have been created, so check before retrying. ({e!s})"
