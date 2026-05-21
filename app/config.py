import os
from typing import Dict, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env (local dev)
load_dotenv()


class Settings(BaseModel):
    # --- Authentication ---
    API_TOKEN: str = Field(..., description="Bearer token required for API access")

    # --- Database ---
    DB_SERVER: str
    DB_DATABASE: str
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_DRIVER: str = "ODBC Driver 18 for SQL Server"

    # --- Query Constraints ---
    QUERY_ROW_LIMIT: int = 500
    MAX_EXECUTION_TIME_SECONDS: int = 10

    # --- Allowlist ---
    ALLOWED_TABLES_JSON: str = Field(
        ..., description="JSON string defining allowed tables and columns"
    )


def load_settings() -> Settings:
    return Settings(
        API_TOKEN=os.getenv("API_TOKEN", ""),
        DB_SERVER=os.getenv("DB_SERVER", ""),
        DB_DATABASE=os.getenv("DB_DATABASE", ""),
        DB_USERNAME=os.getenv("DB_USERNAME", ""),
        DB_PASSWORD=os.getenv("DB_PASSWORD", ""),
        DB_DRIVER=os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server"),
        QUERY_ROW_LIMIT=int(os.getenv("QUERY_ROW_LIMIT", 500)),
        MAX_EXECUTION_TIME_SECONDS=int(os.getenv("MAX_EXECUTION_TIME_SECONDS", 10)),
        ALLOWED_TABLES_JSON=os.getenv("ALLOWED_TABLES_JSON", "{}"),
    )


settings = load_settings()

import json


def get_allowed_tables() -> Dict[str, List[str]]:
    """
    Parses ALLOWED_TABLES_JSON into a usable dictionary.

    Example format:
    {
        "tickets": ["id", "summary", "status", "board", "closed_date"],
        "companies": ["id", "name"]
    }
    """
    try:
        allowed = json.loads(settings.ALLOWED_TABLES_JSON)

        if not isinstance(allowed, dict):
            raise ValueError("ALLOWED_TABLES_JSON must be a dictionary")

        # Ensure all values are lists
        for table, columns in allowed.items():
            if not isinstance(columns, list):
                raise ValueError(f"Columns for table '{table}' must be a list")

        return allowed

    except Exception as e:
        raise ValueError(f"Invalid ALLOWED_TABLES_JSON: {e}")

def validate_environment():
    """
    Ensure critical environment variables are set.
    This should be called at application startup.
    """
    missing = []

    if not settings.API_TOKEN:
        missing.append("API_TOKEN")
    if not settings.DB_SERVER:
        missing.append("DB_SERVER")
    if not settings.DB_DATABASE:
        missing.append("DB_DATABASE")
    if not settings.DB_USERNAME:
        missing.append("DB_USERNAME")
    if not settings.DB_PASSWORD:
        missing.append("DB_PASSWORD")

    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

def get_row_limit(requested_limit: int) -> int:
    """
    Enforce maximum row limit.
    """
    if requested_limit <= 0:
        return settings.QUERY_ROW_LIMIT

    return min(requested_limit, settings.QUERY_ROW_LIMIT)


def get_execution_timeout() -> int:
    """
    Return configured SQL execution timeout.
    """
    return settings.MAX_EXECUTION_TIME_SECONDS

