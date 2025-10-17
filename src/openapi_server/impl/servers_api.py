# coding: utf-8

from fastapi import HTTPException

from concord.server.apis.servers_api_base import BaseServersApi
from concord.server.models.server_register_request import ServerRegisterRequest
from concord.server.models.server_register_response import ServerRegisterResponse
from services.container import get_server_service


class ServersApiImpl(BaseServersApi):
    """Server registration implementation using the in-memory repository."""

    def __init__(self) -> None:
        self._service = get_server_service()

    async def register_server(
        self,
        server_register_request: ServerRegisterRequest,
    ) -> ServerRegisterResponse:
        if not server_register_request or not server_register_request.name:
            raise HTTPException(status_code=400,
                                detail="Server name is required")
        if not server_register_request.platform:
            raise HTTPException(status_code=400,
                                detail="Platform is required")

        platform_id = self._service.register_server(
            platform=server_register_request.platform,
            name=server_register_request.name,
            auth_token=server_register_request.auth_token,
            description=server_register_request.description or "",
            contact_email=server_register_request.contact_email or "",
            webhook_url=server_register_request.webhook_url or "",
        )
        return ServerRegisterResponse(
            platform_id=platform_id,
            name=server_register_request.name,
            platform=server_register_request.platform,
            status="registered",
        )
