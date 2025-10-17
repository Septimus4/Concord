"""Server registration service."""
from __future__ import annotations

from typing import Optional

from services.graph_repository import GraphRepository


class ServerService:
    """Coordinates platform registration."""

    def __init__(self, repository: GraphRepository) -> None:
        self._repository = repository

    def register_server(
        self,
        *,
        platform: str,
        name: str,
        auth_token: Optional[str] = None,
        description: str = "",
        contact_email: str = "",
        webhook_url: str = "",
    ) -> str:
        platform_id = f"{platform}:{name.lower().replace(' ', '-')}"
        self._repository.register_platform(
            platform_id,
            name=name,
            description=description,
            contact_email=contact_email,
            webhook_url=webhook_url,
            auth_token=auth_token or "",
        )
        return platform_id
