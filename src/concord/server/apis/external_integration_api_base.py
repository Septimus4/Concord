# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from concord.server.models.memory_request import MemoryRequest
from concord.server.models.plugin_response import PluginResponse
from concord.server.models.setup_complete200_response import SetupComplete200Response


class BaseExternalIntegrationApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseExternalIntegrationApi.subclasses = (
            BaseExternalIntegrationApi.subclasses + (cls,)
        )

    async def process_memory(
        self,
        memory_request: MemoryRequest,
    ) -> PluginResponse:
        """Processes incoming memory data from Omi and retrieves channels related to the topics within the memory."""
        ...

    async def setup_complete(
        self,
    ) -> SetupComplete200Response:
        """Indicates that the initial setup for the Concord Channel Finder app is complete."""
        ...
