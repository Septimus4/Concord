# app_lifespan.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from bert.model_manager import ModelManager
from graph.graph import initialize_neo4j


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the BERTopic model and Neo4j connection
    try:
        ModelManager.initialize_model()
    except Exception as exc:  # pragma: no cover - startup fallback
        # The placeholder model is acceptable for the MVP; we simply log.
        print(f"Model initialisation failed, falling back to placeholder: {exc}")

    try:
        initialize_neo4j()  # Initialize Neo4j connection
    except Exception as exc:  # pragma: no cover - optional dependency
        print(f"Neo4j initialisation skipped: {exc}")

    yield
    # Shutdown logic here (if needed)
