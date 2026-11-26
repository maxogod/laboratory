from mcp_server.core.exceptions import AppError
from mcp_server.core.server import OVERWRITES_CONTENT, mcp
from mcp_server.integrations.jira.client import get_jira_client


@mcp.tool(annotations=OVERWRITES_CONTENT)
async def jira_edit_ticket(
    ticket_id: str,
    summary: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
) -> str:
    """Overwrite the summary, description and/or labels of a Jira ticket (issue).

    Read the ticket first and show the user the current and new content before calling
    this. Omit fields that are not changing: a rewritten description loses any formatting
    Markdown cannot express, such as tables, panels, images and mentions. At least one
    field must be given.

    Args:
        ticket_id: The Jira issue key or ID (e.g., "PROJ-123").
        summary: The new title. Omit to keep the current one.
        description: The complete new description, in Markdown. An empty string clears it.
        labels: The complete new list of labels. An empty list clears them.

    Returns:
        A confirmation with the ticket's URL.
    """
    if summary is None and description is None and labels is None:
        return "Error: At least one field ('summary', 'description' or 'labels') must be specified."

    try:
        client = get_jira_client()
        await client.update_issue(ticket_id, summary, description, labels)
        return f"Updated {ticket_id}\n{client.browse_url(ticket_id)}"
    except AppError as e:
        return f"Error: Could not update ticket {ticket_id}. Details: {e!s}"
    except Exception as e:
        return f"Unexpected error updating ticket {ticket_id}. It may still have been updated, so check before retrying. ({e!s})"
