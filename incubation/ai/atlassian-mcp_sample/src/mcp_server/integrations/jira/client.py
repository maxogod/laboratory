from typing import Any

import httpx

from mcp_server.core.config import settings
from mcp_server.core.exceptions import (
    ConfigurationError,
    JiraAuthenticationError,
    JiraError,
    JiraNotFoundError,
    JiraPermissionError,
)
from mcp_server.integrations.jira.adf import markdown_to_adf
from mcp_server.integrations.jira.models import JiraIssue


class JiraClient:
    """Async API client for interacting with Jira Cloud REST API v3."""

    def __init__(self, base_url: str, email: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.api_token = api_token
        self.auth = httpx.BasicAuth(self.email, self.api_token)

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    auth=self.auth,
                    headers=headers,
                    timeout=30.0,
                )
                if response.status_code == 401:
                    raise JiraAuthenticationError(
                        "Jira authentication failed. Please verify your email and API token."
                    )
                elif response.status_code == 403:
                    raise JiraPermissionError(
                        "Jira permission denied. Your API token does not have permission for this resource."
                    )
                elif response.status_code == 404:
                    raise JiraNotFoundError(f"Jira resource not found at: {path}")

                response.raise_for_status()
                if response.status_code == 204:
                    return {}
                return response.json()
            except httpx.HTTPStatusError as e:
                raise JiraError(
                    f"Jira API error ({e.response.status_code}): {e.response.text}"
                ) from e
            except httpx.RequestError as e:
                raise JiraError(f"Failed to connect to Jira server: {e!s}") from e

    async def get_issue(self, issue_key: str) -> JiraIssue:
        """Fetch a single issue by key (e.g., PROJ-123)."""
        path = f"/rest/api/3/issue/{issue_key}"
        data = await self._request("GET", path)
        return JiraIssue.model_validate(data)

    async def search_issues(
        self, query: str | None = None, label: str | None = None
    ) -> list[JiraIssue]:
        """Search backlog issues (not Done) using JQL."""
        jql_parts = []
        if query:
            escaped_query = query.replace('"', '\\"')
            jql_parts.append(f'text ~ "{escaped_query}"')
        if label:
            escaped_label = label.replace('"', '\\"')
            jql_parts.append(f'labels = "{escaped_label}"')

        jql_parts.append("statusCategory != Done")

        jql = " AND ".join(jql_parts)
        path = "/rest/api/3/search/jql"
        params = {
            "jql": jql,
            "maxResults": 50,
            "fields": "summary,description,status,labels,assignee,project",
        }
        data = await self._request("GET", path, params=params)
        issues_data = data.get("issues", [])
        return [JiraIssue.model_validate(issue) for issue in issues_data]

    async def create_issue(
        self,
        project_key: str,
        summary: str,
        issue_type: str,
        description: str | None = None,
        labels: list[str] | None = None,
    ) -> str:
        """Create an issue and return its key."""
        fields: dict[str, Any] = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }
        if description:
            fields["description"] = markdown_to_adf(description)
        if labels:
            fields["labels"] = labels
        data = await self._request(
            "POST", "/rest/api/3/issue", json_data={"fields": fields}
        )
        return data["key"]

    async def update_issue(
        self,
        issue_key: str,
        summary: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
    ) -> None:
        """Overwrite the given fields of an issue, leaving fields passed as None as they are."""
        fields: dict[str, Any] = {}
        if summary is not None:
            fields["summary"] = summary
        if description is not None:
            fields["description"] = (
                markdown_to_adf(description) if description else None
            )
        if labels is not None:
            fields["labels"] = labels
        await self._request(
            "PUT", f"/rest/api/3/issue/{issue_key}", json_data={"fields": fields}
        )

    def browse_url(self, issue_key: str) -> str:
        return f"{self.base_url}/browse/{issue_key}"


_jira_client: JiraClient | None = None


def get_jira_client() -> JiraClient:
    """Lazy factory to get or initialize the Jira client instance."""
    global _jira_client
    if _jira_client is not None:
        return _jira_client

    base_url = settings.jira_base_url
    email = settings.atlassian_email
    api_token = settings.jira_api_token

    if not base_url or not email or not api_token:
        raise ConfigurationError(
            "Jira integration is not configured. "
            "Please ensure JIRA_BASE_URL, ATLASSIAN_EMAIL, and JIRA_API_TOKEN are set in your environment."
        )

    _jira_client = JiraClient(
        base_url=base_url,
        email=email,
        api_token=api_token,
    )
    return _jira_client
