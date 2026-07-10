"""Kubernetes Client — integração com Kubernetes API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PodInfo:
    name: str
    namespace: str
    status: str
    containers: list[str] = field(default_factory=list)
    labels: dict[str, str] = field(default_factory=dict)
    node: str = ""


@dataclass
class DeploymentInfo:
    name: str
    namespace: str
    replicas: int
    ready_replicas: int
    image: str = ""
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class ServiceInfo:
    name: str
    namespace: str
    type: str
    cluster_ip: str = ""
    ports: list[dict[str, Any]] = field(default_factory=list)


class K8sClient:
    """Cliente para interação com Kubernetes API."""

    def __init__(self, kubeconfig_path: str = "", base_url: str = "") -> None:
        self._kubeconfig_path = kubeconfig_path
        self._base_url = base_url or "https://kubernetes.default.svc"
        self._token: str = ""
        self._headers: dict[str, str] = {"Accept": "application/json"}

    def set_token(self, token: str) -> None:
        self._token = token
        self._headers["Authorization"] = f"Bearer {token}"

    async def list_pods(self, namespace: str = "default") -> list[PodInfo]:
        data = await self._request("GET", f"/api/v1/namespaces/{namespace}/pods")
        return [
            PodInfo(
                name=item.get("metadata", {}).get("name", ""),
                namespace=namespace,
                status=item.get("status", {}).get("phase", "Unknown"),
                containers=[c.get("name", "") for c in item.get("spec", {}).get("containers", [])],
                labels=item.get("metadata", {}).get("labels", {}),
                node=item.get("spec", {}).get("nodeName", ""),
            )
            for item in data.get("items", [])
        ]

    async def list_deployments(self, namespace: str = "default") -> list[DeploymentInfo]:
        data = await self._request("GET", f"/apis/apps/v1/namespaces/{namespace}/deployments")
        results = []
        for item in data.get("items", []):
            spec = item.get("spec", {})
            status = item.get("status", {})
            containers = spec.get("template", {}).get("spec", {}).get("containers", [])
            image = containers[0].get("image", "") if containers else ""
            results.append(DeploymentInfo(
                name=item.get("metadata", {}).get("name", ""),
                namespace=namespace,
                replicas=spec.get("replicas", 0),
                ready_replicas=status.get("readyReplicas", 0),
                image=image,
                labels=item.get("metadata", {}).get("labels", {}),
            ))
        return results

    async def list_services(self, namespace: str = "default") -> list[ServiceInfo]:
        data = await self._request("GET", f"/api/v1/namespaces/{namespace}/services")
        return [
            ServiceInfo(
                name=item.get("metadata", {}).get("name", ""),
                namespace=namespace,
                type=item.get("spec", {}).get("type", "ClusterIP"),
                cluster_ip=item.get("spec", {}).get("clusterIP", ""),
                ports=item.get("spec", {}).get("ports", []),
            )
            for item in data.get("items", [])
        ]

    async def scale_deployment(self, name: str, replicas: int, namespace: str = "default") -> None:
        payload = {"spec": {"replicas": replicas}}
        await self._request(
            "PATCH",
            f"/apis/apps/v1/namespaces/{namespace}/deployments/{name}/scale",
            json=payload,
        )

    async def get_pod_logs(self, name: str, namespace: str = "default", tail_lines: int = 100) -> str:
        data = await self._request(
            "GET",
            f"/api/v1/namespaces/{namespace}/pods/{name}/log",
            params={"tailLines": str(tail_lines)},
            raw=True,
        )
        return data if isinstance(data, str) else ""

    async def list_namespaces(self) -> list[str]:
        data = await self._request("GET", "/api/v1/namespaces")
        return [item.get("metadata", {}).get("name", "") for item in data.get("items", [])]

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
        raw: bool = False,
    ) -> Any:
        import httpx

        async with httpx.AsyncClient(base_url=self._base_url, headers=self._headers, verify=False) as client:
            response = await client.request(method, path, params=params, json=json, timeout=30.0)
            if raw:
                return response.text
            response.raise_for_status()
            return response.json()
