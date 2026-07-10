"""Docker Client — integração com Docker Engine API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContainerInfo:
    id: str
    name: str
    image: str
    status: str
    ports: dict[str, str] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class ImageInfo:
    id: str
    tags: list[str] = field(default_factory=list)
    size: int = 0
    created: str = ""


class DockerClient:
    """Cliente para interação com Docker Engine API."""

    def __init__(self, base_url: str = "unix:///var/run/docker.sock") -> None:
        self._base_url = base_url

    async def list_containers(self, all_containers: bool = False) -> list[ContainerInfo]:
        data = await self._request("GET", "/containers/json", params={"all": str(all_containers).lower()})
        return [
            ContainerInfo(
                id=c.get("Id", "")[:12],
                name=c.get("Names", [""])[0].lstrip("/"),
                image=c.get("Image", ""),
                status=c.get("Status", ""),
                ports={str(p.get("PrivatePort", "")): str(p.get("PublicPort", "")) for p in c.get("Ports", [])},
                labels=c.get("Labels", {}),
            )
            for c in data
        ]

    async def create_container(
        self, image: str, name: str = "", env: dict[str, str] | None = None, ports: dict[str, int] | None = None
    ) -> str:
        payload: dict[str, Any] = {"Image": image}
        if env:
            payload["Env"] = [f"{k}={v}" for k, v in env.items()]
        if ports:
            payload["ExposedPorts"] = {f"{p}/tcp": {} for p in ports.values()}
            payload["HostConfig"] = {
                "PortBindings": {f"{cp}/tcp": [{"HostPort": str(hp)}] for hp, cp in ports.items()}
            }
        params: dict[str, str] = {}
        if name:
            params["name"] = name
        data = await self._request("POST", "/containers/create", params=params, json=payload)
        return data.get("Id", "")[:12]

    async def start_container(self, container_id: str) -> None:
        await self._request("POST", f"/containers/{container_id}/start")

    async def stop_container(self, container_id: str, timeout: int = 10) -> None:
        await self._request("POST", f"/containers/{container_id}/stop", params={"t": str(timeout)})

    async def remove_container(self, container_id: str, force: bool = False) -> None:
        await self._request("DELETE", f"/containers/{container_id}", params={"force": str(force).lower()})

    async def container_logs(self, container_id: str, tail: int = 100) -> str:
        data = await self._request(
            "GET", f"/containers/{container_id}/logs",
            params={"stdout": "true", "stderr": "true", "tail": str(tail)},
            raw=True,
        )
        return data if isinstance(data, str) else ""

    async def list_images(self) -> list[ImageInfo]:
        data = await self._request("GET", "/images/json")
        return [
            ImageInfo(
                id=img.get("Id", "")[:19],
                tags=img.get("RepoTags", []) or [],
                size=img.get("Size", 0),
                created=str(img.get("Created", "")),
            )
            for img in data
        ]

    async def build_image(self, dockerfile_path: str, tag: str) -> str:
        raise NotImplementedError("Image build requires tar context — use CLI wrapper")

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
        raw: bool = False,
    ) -> Any:
        import httpx

        if self._base_url.startswith("unix://"):
            transport = httpx.AsyncHTTPTransport(uds=self._base_url.replace("unix://", ""))
            base = "http://localhost"
        else:
            transport = None
            base = self._base_url

        async with httpx.AsyncClient(base_url=base, transport=transport) as client:
            response = await client.request(method, path, params=params, json=json, timeout=30.0)
            if response.status_code == 204:
                return {}
            if raw:
                return response.text
            response.raise_for_status()
            return response.json()
