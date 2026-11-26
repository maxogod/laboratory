from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from mcp_server.core.exceptions import (
    BitbucketAuthenticationError,
    BitbucketError,
    BitbucketNotFoundError,
    BitbucketPermissionError,
)
from mcp_server.integrations.bitbucket.client import BitbucketClient
from mcp_server.integrations.bitbucket.models import (
    BitbucketComment,
    BitbucketCommit,
    BitbucketPullRequest,
)
from mcp_server.integrations.bitbucket.tools.bitbucket_create_pr import (
    bitbucket_create_pr,
)
from mcp_server.integrations.bitbucket.tools.bitbucket_edit_pr import (
    bitbucket_edit_pr,
)
from mcp_server.integrations.bitbucket.tools.bitbucket_get_pr_diff import (
    bitbucket_get_pr_diff,
)
from mcp_server.integrations.bitbucket.tools.bitbucket_read_pr import (
    bitbucket_read_pr,
)

PR_URL = "https://bitbucket.org/test-workspace/test-repo/pull-requests/1"
PR_PAYLOAD = {
    "id": 1,
    "title": "Test PR",
    "description": "This is a test PR.",
    "author": {"display_name": "Test User", "account_id": "123"},
    "state": "OPEN",
    "created_on": "2023-01-01T12:00:00Z",
    "updated_on": "2023-01-01T12:00:00Z",
    "links": {"html": {"href": PR_URL}},
}


def _json_response(payload: dict) -> MagicMock:
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.headers = {"content-type": "application/json"}
    response.json.return_value = payload
    return response


@pytest.mark.asyncio
async def test_bitbucket_client_get_pr_success():
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {
        "id": 1,
        "title": "Test PR",
        "description": "This is a test PR.",
        "author": {"display_name": "Test User", "account_id": "123"},
        "state": "OPEN",
        "created_on": "2023-01-01T12:00:00Z",
        "updated_on": "2023-01-01T12:00:00Z",
    }

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_response

        client = BitbucketClient(
            username="test@example.com",
            token="password",
            workspace="test-workspace",
        )
        pr = await client.get_pull_request("test-repo", 1)

        assert isinstance(pr, BitbucketPullRequest)
        assert pr.id == 1
        assert pr.title == "Test PR"
        mock_req.assert_called_once_with(
            method="GET",
            url="https://api.bitbucket.org/2.0/repositories/test-workspace/test-repo/pullrequests/1",
            params=None,
            json=None,
            auth=client.auth,
            headers={"Accept": "application/json"},
            timeout=30.0,
            follow_redirects=True,
        )


@pytest.mark.asyncio
async def test_bitbucket_client_auth_error():
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 401
    mock_response.headers = {"content-type": "application/json"}
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_response
        client = BitbucketClient("user", "wrong-pass", "ws")
        with pytest.raises(BitbucketAuthenticationError):
            await client.get_pull_request("repo", 1)


@pytest.mark.asyncio
async def test_bitbucket_client_permission_error():
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 403
    mock_response.headers = {"content-type": "application/json"}
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_response
        client = BitbucketClient("user", "pass", "ws")
        with pytest.raises(BitbucketPermissionError):
            await client.get_pull_request("repo", 1)


@pytest.mark.asyncio
async def test_bitbucket_client_not_found_error():
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 404
    mock_response.headers = {"content-type": "application/json"}
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_response
        client = BitbucketClient("user", "pass", "ws")
        with pytest.raises(BitbucketNotFoundError):
            await client.get_pull_request("repo", 999)


@pytest.mark.asyncio
async def test_bitbucket_read_pr_tool_includes_metadata_commits_and_comments():
    mock_client = MagicMock()
    mock_client.get_pull_request = AsyncMock(
        return_value=BitbucketPullRequest.model_validate(PR_PAYLOAD)
    )
    mock_client.get_pull_request_commits = AsyncMock(
        return_value=[
            BitbucketCommit.model_validate(
                {
                    "hash": "a1b2c3d4",
                    "message": "Initial commit",
                    "author": {
                        "raw": "Test User <test@example.com>",
                        "user": {"display_name": "Test User", "account_id": "123"},
                    },
                    "date": "2023-01-01T12:00:00Z",
                }
            ),
            BitbucketCommit.model_validate(
                {
                    "hash": "e5f6a7b8",
                    "message": "Follow-up",
                    "author": {"raw": "No Account <none@example.com>"},
                    "date": "2023-01-02T12:00:00Z",
                }
            ),
        ]
    )
    mock_client.get_pull_request_comments = AsyncMock(
        return_value=[
            BitbucketComment.model_validate(
                {
                    "id": 1,
                    "content": {
                        "raw": "First comment",
                        "html": "",
                        "markup": "markdown",
                    },
                    "user": {"display_name": "Another User", "account_id": "456"},
                    "created_on": "2023-01-01T13:00:00Z",
                }
            )
        ]
    )

    with patch(
        "mcp_server.integrations.bitbucket.tools.bitbucket_read_pr.get_bitbucket_client",
        return_value=mock_client,
    ):
        result = await bitbucket_read_pr("test-repo", 1)

    assert "PR #1: Test PR (State: OPEN)" in result
    assert "Author: Test User" in result
    assert "Description:\nThis is a test PR." in result
    assert "Commits (2):" in result
    assert "- a1b2c3d by Test User on 2023-01-01: Initial commit" in result
    assert (
        "- e5f6a7b by No Account <none@example.com> on 2023-01-02: Follow-up" in result
    )
    assert "Comments (1):" in result
    assert "First comment" in result


@pytest.mark.asyncio
async def test_bitbucket_read_pr_tool_without_commits_or_comments():
    mock_client = MagicMock()
    mock_client.get_pull_request = AsyncMock(
        return_value=BitbucketPullRequest.model_validate(PR_PAYLOAD)
    )
    mock_client.get_pull_request_commits = AsyncMock(return_value=[])
    mock_client.get_pull_request_comments = AsyncMock(return_value=[])

    with patch(
        "mcp_server.integrations.bitbucket.tools.bitbucket_read_pr.get_bitbucket_client",
        return_value=mock_client,
    ):
        result = await bitbucket_read_pr("test-repo", 1)

    assert "No commits found." in result
    assert "No comments found." in result


@pytest.mark.asyncio
async def test_bitbucket_read_pr_tool_reports_commit_fetch_failure():
    mock_client = MagicMock()
    mock_client.get_pull_request = AsyncMock(
        return_value=BitbucketPullRequest.model_validate(PR_PAYLOAD)
    )
    mock_client.get_pull_request_commits = AsyncMock(
        side_effect=BitbucketPermissionError("denied")
    )
    mock_client.get_pull_request_comments = AsyncMock(return_value=[])

    with patch(
        "mcp_server.integrations.bitbucket.tools.bitbucket_read_pr.get_bitbucket_client",
        return_value=mock_client,
    ):
        result = await bitbucket_read_pr("test-repo", 1)

    assert "Error: Could not read pull request #1" in result
    assert "denied" in result


@pytest.mark.asyncio
async def test_bitbucket_client_parses_commits_page_without_page_number():
    mock_response = _json_response(
        {
            "pagelen": 10,
            "values": [
                {
                    "hash": "a1b2c3d4",
                    "message": "Initial commit",
                    "author": {"raw": "Test User <test@example.com>"},
                    "date": "2023-01-01T12:00:00Z",
                }
            ],
        }
    )

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_response
        client = BitbucketClient("user", "pass", "ws")
        commits = await client.get_pull_request_commits("repo", 1)

    assert [commit.hash for commit in commits] == ["a1b2c3d4"]


@pytest.mark.asyncio
async def test_bitbucket_client_create_pr_sends_branches_and_description():
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = _json_response(PR_PAYLOAD)
        client = BitbucketClient("user", "pass", "ws")
        pr = await client.create_pull_request(
            "repo", "Test PR", "feature", "develop", "Body", True
        )

    _, kwargs = mock_req.call_args
    assert kwargs["method"] == "POST"
    assert kwargs["url"].endswith("/repositories/ws/repo/pullrequests")
    assert kwargs["json"] == {
        "title": "Test PR",
        "description": "Body",
        "source": {"branch": {"name": "feature"}},
        "destination": {"branch": {"name": "develop"}},
        "close_source_branch": True,
    }
    assert pr.html_url == PR_URL


@pytest.mark.asyncio
async def test_bitbucket_client_create_pr_defaults_to_main_branch():
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = _json_response(PR_PAYLOAD)
        client = BitbucketClient("user", "pass", "ws")
        await client.create_pull_request("repo", "Test PR", "feature")

    assert "destination" not in mock_req.call_args.kwargs["json"]


@pytest.mark.asyncio
async def test_bitbucket_client_update_pr_keeps_reviewers_and_untouched_fields():
    current = {**PR_PAYLOAD, "reviewers": [{"uuid": "{reviewer-1}"}]}
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.side_effect = [_json_response(current), _json_response(current)]
        client = BitbucketClient("user", "pass", "ws")
        await client.update_pull_request("repo", 1, title="New title")

    _, kwargs = mock_req.call_args
    assert kwargs["method"] == "PUT"
    assert kwargs["url"].endswith("/repositories/ws/repo/pullrequests/1")
    assert kwargs["json"] == {
        "title": "New title",
        "description": "This is a test PR.",
        "reviewers": [{"uuid": "{reviewer-1}"}],
    }


@pytest.mark.asyncio
async def test_bitbucket_client_update_pr_can_clear_description():
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.side_effect = [_json_response(PR_PAYLOAD), _json_response(PR_PAYLOAD)]
        client = BitbucketClient("user", "pass", "ws")
        await client.update_pull_request("repo", 1, description="")

    assert mock_req.call_args.kwargs["json"]["description"] == ""


@pytest.mark.asyncio
async def test_bitbucket_create_pr_tool_returns_url():
    mock_client = MagicMock()
    mock_client.create_pull_request = AsyncMock(
        return_value=BitbucketPullRequest.model_validate(PR_PAYLOAD)
    )

    with patch(
        "mcp_server.integrations.bitbucket.tools.bitbucket_create_pr.get_bitbucket_client",
        return_value=mock_client,
    ):
        result = await bitbucket_create_pr("test-repo", "Test PR", "feature")

    assert result == f"Created PR #1: Test PR\n{PR_URL}"


@pytest.mark.asyncio
async def test_bitbucket_create_pr_tool_reports_api_error():
    mock_client = MagicMock()
    mock_client.create_pull_request = AsyncMock(
        side_effect=BitbucketError("source branch not found")
    )

    with patch(
        "mcp_server.integrations.bitbucket.tools.bitbucket_create_pr.get_bitbucket_client",
        return_value=mock_client,
    ):
        result = await bitbucket_create_pr("test-repo", "Test PR", "missing")

    assert "Error: Could not create the pull request" in result
    assert "source branch not found" in result


@pytest.mark.asyncio
async def test_bitbucket_edit_pr_tool_requires_a_field():
    result = await bitbucket_edit_pr("test-repo", 1)
    assert "Error: At least one field" in result


@pytest.mark.asyncio
async def test_bitbucket_edit_pr_tool_returns_url():
    mock_client = MagicMock()
    mock_client.update_pull_request = AsyncMock(
        return_value=BitbucketPullRequest.model_validate(PR_PAYLOAD)
    )

    with patch(
        "mcp_server.integrations.bitbucket.tools.bitbucket_edit_pr.get_bitbucket_client",
        return_value=mock_client,
    ):
        result = await bitbucket_edit_pr("test-repo", 1, title="Test PR")

    mock_client.update_pull_request.assert_called_once_with(
        "test-repo", 1, "Test PR", None
    )
    assert result == f"Updated PR #1: Test PR\n{PR_URL}"


@pytest.mark.asyncio
async def test_bitbucket_get_pr_diff_tool_success():
    mock_client = MagicMock()
    mock_client.get_pull_request_diff = AsyncMock(
        return_value="diff --git a/file b/file"
    )

    with patch(
        "mcp_server.integrations.bitbucket.tools.bitbucket_get_pr_diff.get_bitbucket_client",
        return_value=mock_client,
    ):
        result = await bitbucket_get_pr_diff("test-repo", 1)
        assert "diff --git a/file b/file" in result
