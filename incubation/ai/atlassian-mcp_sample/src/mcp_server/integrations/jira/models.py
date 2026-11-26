from typing import Any

from pydantic import BaseModel, Field

from mcp_server.integrations.jira.adf import parse_adf_to_text


class JiraProject(BaseModel):
    id: str
    key: str
    name: str


class JiraStatus(BaseModel):
    id: str
    name: str


class JiraUser(BaseModel):
    accountId: str
    displayName: str
    emailAddress: str | None = None


class JiraIssueFields(BaseModel):
    summary: str
    description: dict[str, Any] | None = None
    status: JiraStatus
    labels: list[str] = Field(default_factory=list)
    assignee: JiraUser | None = None
    project: JiraProject


class JiraIssue(BaseModel):
    id: str
    key: str
    fields: JiraIssueFields

    def get_plain_description(self) -> str:
        """Parses description from ADF to plain text / Markdown."""
        return parse_adf_to_text(self.fields.description)
