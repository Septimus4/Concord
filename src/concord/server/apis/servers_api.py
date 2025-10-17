# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from concord.server.apis.servers_api_base import BaseServersApi
import openapi_server.impl

from fastapi import (  # noqa: F401
    APIRouter, Body, Cookie, Depends, Form, Header, HTTPException, Path, Query,
    Response, Security, status,
)

from concord.server.models.extra_models import TokenModel  # noqa: F401
from concord.server.models.server_register_request import ServerRegisterRequest
from concord.server.models.server_register_response import ServerRegisterResponse

router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/servers/register",
    responses={
        201: {
            "model": ServerRegisterResponse,
            "description": "Server/group registered successfully."
        },
        400: {
            "description": "Invalid input data or missing required fields."
        },
        409: {
            "description":
            "Conflict if a server/group with the same name exists."
        },
    },
    tags=["servers"],
    summary="Register a new server/group",
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def register_server(
    server_register_request: ServerRegisterRequest = Body(None,
                                                          description=""),
) -> ServerRegisterResponse:
    """Registers a new server/group with configurable metadata, including platform and authentication token."""
    if not BaseServersApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseServersApi.subclasses[0]().register_server(
        server_register_request)
