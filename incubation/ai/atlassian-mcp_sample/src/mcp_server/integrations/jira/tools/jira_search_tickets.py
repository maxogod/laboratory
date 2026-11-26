from mcp_server.core.exceptions import AppError
from mcp_server.core.server import READ_ONLY, mcp
from mcp_server.integrations.jira.client import get_jira_client


@mcp.tool(annotations=READ_ONLY)
async def jira_search_tickets(
    query: str | None = None, label: str | None = None
) -> str:
    """List and search for Jira tickets (issues) in the backlog (not Done) with a given topic/query or labels.

    At least one search parameter (query or label) must be specified.

    Args:
        query: Keywords or phrases to search for in ticket fields (e.g., "auth bug").
        label: A specific label to filter issues by.

    Returns:
        A formatted list of matching issues, or a message if none found.
    """
    if not query and not label:
        return "Error: At least one search parameter ('query' or 'label') must be specified."

    try:
        client = get_jira_client()
        issues = await client.search_issues(query=query, label=label)

        if not issues:
            criteria = []
            if query:
                criteria.append(f"query '{query}'")
            if label:
                criteria.append(f"label '{label}'")
            return f"No backlog tickets found matching: {' and '.join(criteria)}"

        result_lines = [f"Found {len(issues)} backlog ticket(s):", ""]
        for issue in issues:
            status = issue.fields.status.name
            summary = issue.fields.summary
            result_lines.append(f"- [{issue.key}] {summary} (Status: {status})")

        return "\n".join(result_lines)
    except AppError as e:
        return f"Error: Could not search tickets. The integration may be unconfigured, or you lack permissions. Details: {e!s}"
    except Exception as e:
        return f"Unexpected error searching tickets. Please try again. ({e!s})"
