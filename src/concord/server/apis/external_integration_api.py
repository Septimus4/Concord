# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from concord.server.apis.external_integration_api_base import BaseExternalIntegrationApi
import openapi_server.impl

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    Security,
    status,
)

from concord.server.models.extra_models import TokenModel  # noqa: F401
from concord.server.models.memory_request import MemoryRequest
from concord.server.models.plugin_response import PluginResponse
from concord.server.models.setup_complete200_response import SetupComplete200Response

router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/process-memory",
    responses={
        200: {
            "model": PluginResponse,
            "description": "Related channels list retrieved for processed memory data.",
        },
        400: {"description": "Invalid input data."},
    },
    tags=["external_integration"],
    summary="Process memory data and retrieve related channels",
    response_model_by_alias=True,
)
async def process_memory(
    memory_request: MemoryRequest = Body(None, description=""),
) -> PluginResponse:
    """Processes incoming memory data from Omi and retrieves channels related to the topics within the memory."""
    if not BaseExternalIntegrationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseExternalIntegrationApi.subclasses[0]().process_memory(
        memory_request
    )


@router.get(
    "/setup-complete",
    responses={
        200: {
            "model": SetupComplete200Response,
            "description": "Setup completion acknowledgment.",
        },
        500: {"description": "Server error if setup could not be verified."},
    },
    tags=["external_integration"],
    summary="Confirm setup completion for Concord Channel Finder",
    response_model_by_alias=True,
)
async def setup_complete() -> SetupComplete200Response:
    """Indicates that the initial setup for the Concord Channel Finder app is complete."""
    if not BaseExternalIntegrationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseExternalIntegrationApi.subclasses[0]().setup_complete()
