from typing import Any, final

import httpx

from mcp_server.core.config import settings
from mcp_server.core.exceptions import (
    BitbucketAuthenticationError,
    BitbucketError,
    BitbucketNotFoundError,
    BitbucketPermissionError,
    ConfigurationError,
)
from mcp_server.integrations.bitbucket.models import (
    BitbucketComment,
    BitbucketCommit,
    BitbucketPullRequest,
    PaginatedResponse,
)


@final
class BitbucketClient:
    """Async API client for interacting with Bitbucket Cloud REST API v2."""

    BASE_URL = "https://api.bitbucket.org/2.0"

    def __init__(self, username: str, token: str, workspace: str):
        self.workspace = workspace
        self.auth = httpx.BasicAuth(username, token)

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | str:
        url = f"{self.BASE_URL}{path}"
        headers = {"Accept": "application/json"}
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
                    follow_redirects=True,
                )
                if response.status_code == 401:
                    raise BitbucketAuthenticationError(
                        "Bitbucket authentication failed. Please verify your username and token."
                    )
                elif response.status_code == 403:
                    raise BitbucketPermissionError(
                        "Bitbucket permission denied. Your credentials do not have permission for this resource."
                    )
                elif response.status_code == 404:
                    raise BitbucketNotFoundError(
                        f"Bitbucket resource not found at: {path}"
                    )

                response.raise_for_status()

                # The "diff" endpoint returns a text response
                if response.headers.get("content-type") == "text/plain":
                    return response.text
                return response.json()
            except httpx.HTTPStatusError as e:
                raise BitbucketError(
                    f"Bitbucket API error ({e.response.status_code}): {e.response.text}"
                ) from e
            except httpx.RequestError as e:
                raise BitbucketError(
                    f"Failed to connect to Bitbucket server: {e!s}"
                ) from e

    async def get_pull_request(
        self, repo_slug: str, pull_request_id: int
    ) -> BitbucketPullRequest:
        """Fetch a single pull request."""
        path = (
            f"/repositories/{self.workspace}/{repo_slug}/pullrequests/{pull_request_id}"
        )
        data = await self._request("GET", path)
        return BitbucketPullRequest.model_validate(data)

    async def get_pull_request_comments(
        self, repo_slug: str, pull_request_id: int
    ) -> list[BitbucketComment]:
        """Fetch all comments for a given pull request."""
        path = f"/repositories/{self.workspace}/{repo_slug}/pullrequests/{pull_request_id}/comments"
        data = await self._request("GET", path)
        paginated_response = PaginatedResponse.model_validate(data)
        return [
            BitbucketComment.model_validate(item) for item in paginated_response.values
        ]

    async def get_pull_request_commits(
        self, repo_slug: str, pull_request_id: int
    ) -> list[BitbucketCommit]:
        """Fetch all commits for a given pull request."""
        path = f"/repositories/{self.workspace}/{repo_slug}/pullrequests/{pull_request_id}/commits"
        data = await self._request("GET", path)
        paginated_response = PaginatedResponse.model_validate(data)
        return [
            BitbucketCommit.model_validate(item) for item in paginated_response.values
        ]

    async def get_pull_request_diff(self, repo_slug: str, pull_request_id: int) -> str:
        """Fetch the diff for a given pull request."""
        path = f"/repositories/{self.workspace}/{repo_slug}/pullrequests/{pull_request_id}/diff"
        diff_text = await self._request("GET", path)
        if not isinstance(diff_text, str):
            raise BitbucketError("Failed to retrieve diff, expected text response.")
        return diff_text

    async def create_pull_request(
        self,
        repo_slug: str,
        title: str,
        source_branch: str,
        destination_branch: str | None = None,
        description: str = "",
        close_source_branch: bool = False,
    ) -> BitbucketPullRequest:
        """Create a pull request, targeting the repository's main branch by default."""
        payload: dict[str, Any] = {
            "title": title,
            "description": description,
            "source": {"branch": {"name": source_branch}},
            "close_source_branch": close_source_branch,
        }
        if destination_branch:
            payload["destination"] = {"branch": {"name": destination_branch}}
        path = f"/repositories/{self.workspace}/{repo_slug}/pullrequests"
        data = await self._request("POST", path, json_data=payload)
        return BitbucketPullRequest.model_validate(data)

    async def update_pull_request(
        self,
        repo_slug: str,
        pull_request_id: int,
        title: str | None = None,
        description: str | None = None,
    ) -> BitbucketPullRequest:
        """Overwrite the title and/or description of a pull request."""
        current = await self.get_pull_request(repo_slug, pull_request_id)
        # Bitbucket can clear reviewers that a PUT omits, so they are always resent.
        payload = {
            "title": current.title if title is None else title,
            "description": current.description if description is None else description,
            "reviewers": [{"uuid": reviewer.uuid} for reviewer in current.reviewers],
        }
        path = (
            f"/repositories/{self.workspace}/{repo_slug}/pullrequests/{pull_request_id}"
        )
        data = await self._request("PUT", path, json_data=payload)
        return BitbucketPullRequest.model_validate(data)


_bitbucket_client: BitbucketClient | None = None


def get_bitbucket_client() -> BitbucketClient:
    """Lazy factory to get or initialize the Bitbucket client instance."""
    global _bitbucket_client
    if _bitbucket_client is not None:
        return _bitbucket_client

    if not settings.is_bitbucket_enabled:
        raise ConfigurationError(
            "Bitbucket integration is not configured. Please ensure BITBUCKET_WORKSPACE, ATLASSIAN_EMAIL, and BITBUCKET_TOKEN are set."
        )

    assert settings.atlassian_email is not None
    assert settings.bitbucket_token is not None
    assert settings.bitbucket_workspace is not None

    _bitbucket_client = BitbucketClient(
        username=settings.atlassian_email,
        token=settings.bitbucket_token,
        workspace=settings.bitbucket_workspace,
    )
    return _bitbucket_client
