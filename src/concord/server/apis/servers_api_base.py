# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from concord.server.models.server_register_request import ServerRegisterRequest
from concord.server.models.server_register_response import ServerRegisterResponse


class BaseServersApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseServersApi.subclasses = BaseServersApi.subclasses + (cls,)

    async def register_server(
        self,
        server_register_request: ServerRegisterRequest,
    ) -> ServerRegisterResponse:
        """Registers a new server/group with configurable metadata, including platform and authentication token."""
        ...
