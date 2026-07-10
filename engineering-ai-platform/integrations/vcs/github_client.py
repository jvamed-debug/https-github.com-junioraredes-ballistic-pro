"""GitHub Client — integração com GitHub API."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PRState(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


@dataclass
class GitHubRepo:
    owner: str
    name: str
    default_branch: str = "main"
    url: str = ""


@dataclass
class PullRequest:
    number: int
    title: str
    body: str
    state: PRState
    source_branch: str
    target_branch: str
    author: str = ""
    labels: list[str] = field(default_factory=list)
    reviewers: list[str] = field(default_factory=list)


@dataclass
class CommitInfo:
    sha: str
    message: str
    author: str
    files_changed: list[str] = field(default_factory=list)


class GitHubClient:
    """Cliente para interação com GitHub API."""

    def __init__(self, token: str = "", base_url: str = "https://api.github.com") -> None:
        self._token = token
        self._base_url = base_url
        self._headers: dict[str, str] = {}
        if token:
            self._headers["Authorization"] = f"Bearer {token}"
            self._headers["Accept"] = "application/vnd.github+json"

    async def get_repo(self, owner: str, name: str) -> GitHubRepo:
        data = await self._request("GET", f"/repos/{owner}/{name}")
        return GitHubRepo(
            owner=data.get("owner", {}).get("login", owner),
            name=data.get("name", name),
            default_branch=data.get("default_branch", "main"),
            url=data.get("html_url", ""),
        )

    async def list_pull_requests(
        self, repo: GitHubRepo, state: str = "open"
    ) -> list[PullRequest]:
        data = await self._request(
            "GET", f"/repos/{repo.owner}/{repo.name}/pulls", params={"state": state}
        )
        return [self._parse_pr(pr) for pr in data]

    async def create_pull_request(
        self,
        repo: GitHubRepo,
        title: str,
        body: str,
        source_branch: str,
        target_branch: str | None = None,
    ) -> PullRequest:
        payload = {
            "title": title,
            "body": body,
            "head": source_branch,
            "base": target_branch or repo.default_branch,
        }
        data = await self._request(
            "POST", f"/repos/{repo.owner}/{repo.name}/pulls", json=payload
        )
        return self._parse_pr(data)

    async def get_commit(self, repo: GitHubRepo, sha: str) -> CommitInfo:
        data = await self._request(
            "GET", f"/repos/{repo.owner}/{repo.name}/commits/{sha}"
        )
        return CommitInfo(
            sha=data.get("sha", sha),
            message=data.get("commit", {}).get("message", ""),
            author=data.get("commit", {}).get("author", {}).get("name", ""),
            files_changed=[f.get("filename", "") for f in data.get("files", [])],
        )

    async def list_branches(self, repo: GitHubRepo) -> list[str]:
        data = await self._request(
            "GET", f"/repos/{repo.owner}/{repo.name}/branches"
        )
        return [b.get("name", "") for b in data]

    async def get_file_content(
        self, repo: GitHubRepo, path: str, ref: str | None = None
    ) -> str:
        import base64

        params: dict[str, str] = {}
        if ref:
            params["ref"] = ref
        data = await self._request(
            "GET", f"/repos/{repo.owner}/{repo.name}/contents/{path}", params=params
        )
        content = data.get("content", "")
        return base64.b64decode(content).decode("utf-8") if content else ""

    def _parse_pr(self, data: dict[str, Any]) -> PullRequest:
        return PullRequest(
            number=data.get("number", 0),
            title=data.get("title", ""),
            body=data.get("body", ""),
            state=PRState(data.get("state", "open")),
            source_branch=data.get("head", {}).get("ref", ""),
            target_branch=data.get("base", {}).get("ref", ""),
            author=data.get("user", {}).get("login", ""),
            labels=[l.get("name", "") for l in data.get("labels", [])],
            reviewers=[r.get("login", "") for r in data.get("requested_reviewers", [])],
        )

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        import httpx

        async with httpx.AsyncClient(base_url=self._base_url, headers=self._headers) as client:
            response = await client.request(method, path, params=params, json=json)
            response.raise_for_status()
            return response.json()
