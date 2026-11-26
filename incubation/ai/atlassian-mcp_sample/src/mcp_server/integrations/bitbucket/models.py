from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BitbucketUser(BaseModel):
    display_name: str | None = Field(None, alias="display_name")
    account_id: str | None = Field(None, alias="account_id")
    uuid: str | None = None


class BitbucketRawAuthor(BaseModel):
    raw: str
    user: BitbucketUser | None = None


class BitbucketCommit(BaseModel):
    hash: str
    message: str
    author: BitbucketRawAuthor
    date: datetime


class BitbucketCommentContent(BaseModel):
    raw: str
    html: str
    markup: str


class BitbucketComment(BaseModel):
    id: int
    content: BitbucketCommentContent
    user: BitbucketUser
    created_on: datetime


class BitbucketPullRequest(BaseModel):
    id: int
    title: str
    description: str = ""
    author: BitbucketUser
    state: str
    created_on: datetime
    updated_on: datetime
    reviewers: list[BitbucketUser] = Field(default_factory=list)
    links: dict[str, Any] = Field(default_factory=dict)

    @property
    def html_url(self) -> str:
        return self.links.get("html", {}).get("href", "")


class PaginatedResponse(BaseModel):
    values: list[Any]
    page: int | None = None
    size: int | None = None
    next: str | None = None
