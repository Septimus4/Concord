# graph.py
import os

try:  # pragma: no cover - optional dependency
    from neomodel import config
except Exception:  # pragma: no cover
    config = None

# Get the connection details from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "localhost:7687")  # No `bolt://` prefix here
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "dev-password")


def initialize_neo4j():
    if config is None:
        return
    # Add the 'bolt://' prefix and format the URL with credentials
    config.DATABASE_URL = f"bolt://{NEO4J_USER}:{NEO4J_PASSWORD}@{DATABASE_URL}"
