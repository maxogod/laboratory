from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from mcp_server.core.exceptions import (
    JiraAuthenticationError,
    JiraError,
    JiraNotFoundError,
    JiraPermissionError,
)
from mcp_server.integrations.jira.adf import markdown_to_adf, parse_adf_to_text
from mcp_server.integrations.jira.client import JiraClient
from mcp_server.integrations.jira.models import JiraIssue
from mcp_server.integrations.jira.tools.jira_create_ticket import (
    jira_create_ticket,
)
from mcp_server.integrations.jira.tools.jira_edit_ticket import (
    jira_edit_ticket,
)
from mcp_server.integrations.jira.tools.jira_read_ticket import (
    jira_read_ticket,
)
from mcp_server.integrations.jira.tools.jira_search_tickets import (
    jira_search_tickets,
)


def test_parse_adf_to_text_empty():
    assert parse_adf_to_text(None) == ""
    assert parse_adf_to_text("") == ""
    assert parse_adf_to_text({}) == ""


def test_parse_adf_to_text_plain_string():
    assert parse_adf_to_text("hello") == "hello"


def test_parse_adf_to_text_paragraph():
    adf = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "Hello world"}],
            }
        ],
    }
    assert parse_adf_to_text(adf) == "Hello world\n"


def test_parse_adf_to_text_bullet_list():
    adf = {
        "type": "bulletList",
        "content": [
            {
                "type": "listItem",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "First point"}],
                    }
                ],
            },
            {
                "type": "listItem",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Second point"}],
                    }
                ],
            },
        ],
    }
    assert parse_adf_to_text(adf) == "* First point\n* Second point\n"


@pytest.mark.asyncio
async def test_jira_client_get_issue_success():
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "10001",
        "key": "PROJ-123",
        "fields": {
            "summary": "Implement auth middleware",
            "description": {
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "This is a draft"}],
                    }
                ],
            },
            "status": {"id": "1", "name": "To Do"},
            "labels": ["security"],
            "assignee": {"accountId": "usr-1", "displayName": "Alice Smith"},
            "project": {"id": "p-1", "key": "PROJ", "name": "Main Project"},
        },
    }

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_response

        client = JiraClient(
            base_url="https://test.atlassian.net",
            email="test@test.com",
            api_token="token",
        )
        issue = await client.get_issue("PROJ-123")

        assert issue.id == "10001"
        assert issue.key == "PROJ-123"
        assert issue.fields.summary == "Implement auth middleware"
        assert issue.get_plain_description() == "This is a draft\n"

        mock_req.assert_called_once()
        _, kwargs = mock_req.call_args
        assert kwargs["url"] == "https://test.atlassian.net/rest/api/3/issue/PROJ-123"
        assert kwargs["method"] == "GET"


@pytest.mark.asyncio
async def test_jira_client_auth_error():
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 401

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_response
        client = JiraClient(
            base_url="https://test.atlassian.net",
            email="test@test.com",
            api_token="token",
        )

        with pytest.raises(JiraAuthenticationError):
            await client.get_issue("PROJ-123")


@pytest.mark.asyncio
async def test_jira_client_permission_error():
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 403

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_response
        client = JiraClient(
            base_url="https://test.atlassian.net",
            email="test@test.com",
            api_token="token",
        )

        with pytest.raises(JiraPermissionError):
            await client.get_issue("PROJ-123")


@pytest.mark.asyncio
async def test_jira_client_not_found_error():
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 404

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_response
        client = JiraClient(
            base_url="https://test.atlassian.net",
            email="test@test.com",
            api_token="token",
        )

        with pytest.raises(JiraNotFoundError):
            await client.get_issue("PROJ-999")


@pytest.mark.asyncio
async def test_jira_client_search_success():
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "issues": [
            {
                "id": "10001",
                "key": "PROJ-123",
                "fields": {
                    "summary": "First ticket",
                    "description": None,
                    "status": {"id": "1", "name": "To Do"},
                    "labels": ["bug"],
                    "assignee": None,
                    "project": {"id": "p-1", "key": "PROJ", "name": "Main"},
                },
            }
        ]
    }

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_response
        client = JiraClient(
            base_url="https://test.atlassian.net",
            email="test@test.com",
            api_token="token",
        )

        results = await client.search_issues(query="bug", label="triage")
        assert len(results) == 1
        assert results[0].key == "PROJ-123"

        mock_req.assert_called_once()
        _, kwargs = mock_req.call_args
        assert kwargs["url"] == "https://test.atlassian.net/rest/api/3/search/jql"
        jql = kwargs["params"]["jql"]
        assert 'text ~ "bug"' in jql
        assert 'labels = "triage"' in jql
        assert "statusCategory != Done" in jql
        assert (
            kwargs["params"]["fields"]
            == "summary,description,status,labels,assignee,project"
        )


@pytest.mark.asyncio
async def test_jira_read_ticket_tool_success():
    mock_issue = JiraIssue.model_validate(
        {
            "id": "10001",
            "key": "PROJ-123",
            "fields": {
                "summary": "Mock Issue Summary",
                "description": {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Mock description text"}],
                },
                "status": {"id": "1", "name": "In Progress"},
                "labels": ["bug"],
                "assignee": {"accountId": "usr-1", "displayName": "Bob"},
                "project": {"id": "p-1", "key": "PROJ", "name": "Main Project"},
            },
        }
    )
    mock_client = MagicMock()
    mock_client.get_issue = AsyncMock(return_value=mock_issue)

    with patch(
        "mcp_server.integrations.jira.tools.jira_read_ticket.get_jira_client",
        return_value=mock_client,
    ):
        result = await jira_read_ticket("PROJ-123")
        assert "Ticket: PROJ-123" in result
        assert "Summary: Mock Issue Summary" in result
        assert "Status: In Progress" in result
        assert "Mock description text" in result


@pytest.mark.asyncio
async def test_jira_read_ticket_tool_error_handling():
    mock_client = MagicMock()
    mock_client.get_issue.side_effect = JiraNotFoundError("Resource not found")

    with patch(
        "mcp_server.integrations.jira.tools.jira_read_ticket.get_jira_client",
        return_value=mock_client,
    ):
        result = await jira_read_ticket("PROJ-999")
        assert "Error: Could not find ticket PROJ-999" in result
        assert "Resource not found" in result


@pytest.mark.asyncio
async def test_jira_search_tickets_tool_no_criteria():
    result = await jira_search_tickets()
    assert "Error: At least one search parameter" in result


@pytest.mark.asyncio
async def test_jira_search_tickets_tool_success():
    mock_issue = JiraIssue.model_validate(
        {
            "id": "10001",
            "key": "PROJ-123",
            "fields": {
                "summary": "Mock Issue Summary",
                "description": None,
                "status": {"id": "1", "name": "To Do"},
                "labels": ["bug"],
                "assignee": None,
                "project": {"id": "p-1", "key": "PROJ", "name": "Main Project"},
            },
        }
    )
    mock_client = MagicMock()
    mock_client.search_issues = AsyncMock(return_value=[mock_issue])

    with patch(
        "mcp_server.integrations.jira.tools.jira_search_tickets.get_jira_client",
        return_value=mock_client,
    ):
        result = await jira_search_tickets(query="Mock")
        assert "Found 1 backlog ticket(s)" in result
        assert "- [PROJ-123] Mock Issue Summary (Status: To Do)" in result


@pytest.mark.asyncio
async def test_jira_search_tickets_tool_no_results():
    mock_client = MagicMock()
    mock_client.search_issues = AsyncMock(return_value=[])

    with patch(
        "mcp_server.integrations.jira.tools.jira_search_tickets.get_jira_client",
        return_value=mock_client,
    ):
        result = await jira_search_tickets(query="Missing")
        assert "No backlog tickets found matching: query 'Missing'" in result


def _text(text: str, *marks: dict) -> dict:
    node: dict = {"type": "text", "text": text}
    if marks:
        node["marks"] = list(marks)
    return node


def _paragraph(*content: dict) -> dict:
    return {"type": "paragraph", "content": list(content)}


def test_markdown_to_adf_wraps_content_in_a_document():
    assert markdown_to_adf("Hello") == {
        "type": "doc",
        "version": 1,
        "content": [_paragraph(_text("Hello"))],
    }


def test_markdown_to_adf_empty():
    assert markdown_to_adf("")["content"] == []


def test_markdown_to_adf_paragraphs_keep_line_breaks():
    assert markdown_to_adf("one\ntwo\n\nthree")["content"] == [
        _paragraph(_text("one"), {"type": "hardBreak"}, _text("two")),
        _paragraph(_text("three")),
    ]


def test_markdown_to_adf_headings_and_rule():
    assert markdown_to_adf("## Title\n---")["content"] == [
        {
            "type": "heading",
            "attrs": {"level": 2},
            "content": [_text("Title")],
        },
        {"type": "rule"},
    ]


@pytest.mark.parametrize(
    ("markdown", "list_type"),
    [("- one\n- two", "bulletList"), ("1. one\n2. two", "orderedList")],
)
def test_markdown_to_adf_lists(markdown, list_type):
    assert markdown_to_adf(markdown)["content"] == [
        {
            "type": list_type,
            "content": [
                {"type": "listItem", "content": [_paragraph(_text("one"))]},
                {"type": "listItem", "content": [_paragraph(_text("two"))]},
            ],
        }
    ]


def test_markdown_to_adf_inline_marks():
    content = markdown_to_adf("a **b** *c* `d` [e](https://f.test) 2 * 3 * 4")[
        "content"
    ]
    assert content == [
        _paragraph(
            _text("a "),
            _text("b", {"type": "strong"}),
            _text(" "),
            _text("c", {"type": "em"}),
            _text(" "),
            _text("d", {"type": "code"}),
            _text(" "),
            _text("e", {"type": "link", "attrs": {"href": "https://f.test"}}),
            _text(" 2 * 3 * 4"),
        )
    ]


def test_markdown_to_adf_code_block_is_not_parsed_as_markdown():
    markdown = "before\n```python\n# not a heading\n- not a list\n```\nafter"
    assert markdown_to_adf(markdown)["content"] == [
        _paragraph(_text("before")),
        {
            "type": "codeBlock",
            "attrs": {"language": "python"},
            "content": [_text("# not a heading\n- not a list")],
        },
        _paragraph(_text("after")),
    ]


def test_markdown_to_adf_output_reads_back_as_text():
    adf = markdown_to_adf("# Title\nline one\nline two\n\n- item")
    assert parse_adf_to_text(adf) == "Title\nline one\nline two\n* item\n"


def _jira_client() -> JiraClient:
    return JiraClient(
        base_url="https://test.atlassian.net",
        email="test@test.com",
        api_token="token",
    )


@pytest.mark.asyncio
async def test_jira_client_create_issue_sends_fields():
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": "1", "key": "PROJ-1", "self": "url"}

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_response
        key = await _jira_client().create_issue(
            "PROJ", "Summary", "Bug", "Body", ["backend"]
        )

    assert key == "PROJ-1"
    _, kwargs = mock_req.call_args
    assert kwargs["method"] == "POST"
    assert kwargs["url"] == "https://test.atlassian.net/rest/api/3/issue"
    assert kwargs["json"] == {
        "fields": {
            "project": {"key": "PROJ"},
            "summary": "Summary",
            "issuetype": {"name": "Bug"},
            "description": markdown_to_adf("Body"),
            "labels": ["backend"],
        }
    }


@pytest.mark.asyncio
async def test_jira_client_create_issue_omits_empty_optional_fields():
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": "1", "key": "PROJ-1", "self": "url"}

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_response
        await _jira_client().create_issue("PROJ", "Summary", "Task")

    assert set(mock_req.call_args.kwargs["json"]["fields"]) == {
        "project",
        "summary",
        "issuetype",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("changes", "expected_fields"),
    [
        ({"summary": "New"}, {"summary": "New"}),
        ({"description": "Body"}, {"description": markdown_to_adf("Body")}),
        ({"description": ""}, {"description": None}),
        ({"labels": []}, {"labels": []}),
    ],
)
async def test_jira_client_update_issue_sends_only_changed_fields(
    changes, expected_fields
):
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 204

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_response
        await _jira_client().update_issue("PROJ-1", **changes)

    _, kwargs = mock_req.call_args
    assert kwargs["method"] == "PUT"
    assert kwargs["url"] == "https://test.atlassian.net/rest/api/3/issue/PROJ-1"
    assert kwargs["json"] == {"fields": expected_fields}
    mock_response.json.assert_not_called()


@pytest.mark.asyncio
async def test_jira_create_ticket_tool_returns_url():
    mock_client = MagicMock()
    mock_client.create_issue = AsyncMock(return_value="PROJ-1")
    mock_client.browse_url.return_value = "https://test.atlassian.net/browse/PROJ-1"

    with patch(
        "mcp_server.integrations.jira.tools.jira_create_ticket.get_jira_client",
        return_value=mock_client,
    ):
        result = await jira_create_ticket("PROJ", "Summary", "Task")

    assert result == "Created PROJ-1: Summary\nhttps://test.atlassian.net/browse/PROJ-1"


@pytest.mark.asyncio
async def test_jira_create_ticket_tool_reports_api_error():
    mock_client = MagicMock()
    mock_client.create_issue = AsyncMock(side_effect=JiraError("invalid issue type"))

    with patch(
        "mcp_server.integrations.jira.tools.jira_create_ticket.get_jira_client",
        return_value=mock_client,
    ):
        result = await jira_create_ticket("PROJ", "Summary", "Nope")

    assert "Error: Could not create the ticket in project PROJ" in result
    assert "invalid issue type" in result


@pytest.mark.asyncio
async def test_jira_edit_ticket_tool_requires_a_field():
    result = await jira_edit_ticket("PROJ-1")
    assert "Error: At least one field" in result


@pytest.mark.asyncio
async def test_jira_edit_ticket_tool_passes_changes_to_client():
    mock_client = MagicMock()
    mock_client.update_issue = AsyncMock()
    mock_client.browse_url.return_value = "https://test.atlassian.net/browse/PROJ-1"

    with patch(
        "mcp_server.integrations.jira.tools.jira_edit_ticket.get_jira_client",
        return_value=mock_client,
    ):
        result = await jira_edit_ticket("PROJ-1", description="New body")

    mock_client.update_issue.assert_called_once_with("PROJ-1", None, "New body", None)
    assert result == "Updated PROJ-1\nhttps://test.atlassian.net/browse/PROJ-1"
