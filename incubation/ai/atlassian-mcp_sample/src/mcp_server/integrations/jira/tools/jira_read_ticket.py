from mcp_server.core.exceptions import AppError
from mcp_server.core.server import READ_ONLY, mcp
from mcp_server.integrations.jira.client import get_jira_client


@mcp.tool(annotations=READ_ONLY)
async def jira_read_ticket(ticket_id: str) -> str:
    """Read details of a Jira ticket (issue) by its ID or key (e.g., PROJ-123).

    Args:
        ticket_id: The Jira issue key or ID (e.g., "PROJ-123").

    Returns:
        A detailed summary of the ticket including key, status, summary, and description.
    """
    try:
        client = get_jira_client()
        issue = await client.get_issue(ticket_id)

        assignee_name = (
            issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned"
        )
        labels_str = ", ".join(issue.fields.labels) if issue.fields.labels else "None"
        description = issue.get_plain_description() or "No description provided."

        return (
            f"Ticket: {issue.key}\n"
            f"Project: {issue.fields.project.name} ({issue.fields.project.key})\n"
            f"Summary: {issue.fields.summary}\n"
            f"Status: {issue.fields.status.name}\n"
            f"Assignee: {assignee_name}\n"
            f"Labels: {labels_str}\n"
            f"Description:\n{description}"
        )
    except AppError as e:
        return f"Error: Could not find ticket {ticket_id}. It may not exist, you lack permissions, or the integration is unconfigured. Details: {e!s}"
    except Exception as e:
        return f"Unexpected error reading ticket {ticket_id}. Please try again. ({e!s})"
