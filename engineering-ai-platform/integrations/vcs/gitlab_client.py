"""GitLab Client — integração com GitLab API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GitLabProject:
    id: int
    name: str
    path_with_namespace: str
    default_branch: str = "main"
    web_url: str = ""


@dataclass
class MergeRequest:
    iid: int
    title: str
    description: str
    state: str
    source_branch: str
    target_branch: str
    author: str = ""
    labels: list[str] = field(default_factory=list)


class GitLabClient:
    """Cliente para interação com GitLab API."""

    def __init__(self, token: str = "", base_url: str = "https://gitlab.com/api/v4") -> None:
        self._token = token
        self._base_url = base_url
        self._headers: dict[str, str] = {}
        if token:
            self._headers["PRIVATE-TOKEN"] = token

    async def get_project(self, project_id: int | str) -> GitLabProject:
        data = await self._request("GET", f"/projects/{project_id}")
        return GitLabProject(
            id=data.get("id", 0),
            name=data.get("name", ""),
            path_with_namespace=data.get("path_with_namespace", ""),
            default_branch=data.get("default_branch", "main"),
            web_url=data.get("web_url", ""),
        )

    async def list_merge_requests(
        self, project_id: int | str, state: str = "opened"
    ) -> list[MergeRequest]:
        data = await self._request(
            "GET", f"/projects/{project_id}/merge_requests", params={"state": state}
        )
        return [self._parse_mr(mr) for mr in data]

    async def create_merge_request(
        self,
        project_id: int | str,
        title: str,
        description: str,
        source_branch: str,
        target_branch: str = "main",
    ) -> MergeRequest:
        payload = {
            "title": title,
            "description": description,
            "source_branch": source_branch,
            "target_branch": target_branch,
        }
        data = await self._request(
            "POST", f"/projects/{project_id}/merge_requests", json=payload
        )
        return self._parse_mr(data)

    async def list_branches(self, project_id: int | str) -> list[str]:
        data = await self._request("GET", f"/projects/{project_id}/repository/branches")
        return [b.get("name", "") for b in data]

    async def get_file_content(
        self, project_id: int | str, file_path: str, ref: str = "main"
    ) -> str:
        import base64
        from urllib.parse import quote

        encoded_path = quote(file_path, safe="")
        data = await self._request(
            "GET",
            f"/projects/{project_id}/repository/files/{encoded_path}",
            params={"ref": ref},
        )
        content = data.get("content", "")
        return base64.b64decode(content).decode("utf-8") if content else ""

    def _parse_mr(self, data: dict[str, Any]) -> MergeRequest:
        return MergeRequest(
            iid=data.get("iid", 0),
            title=data.get("title", ""),
            description=data.get("description", ""),
            state=data.get("state", "opened"),
            source_branch=data.get("source_branch", ""),
            target_branch=data.get("target_branch", ""),
            author=data.get("author", {}).get("username", ""),
            labels=data.get("labels", []),
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
