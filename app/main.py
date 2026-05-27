import logging
from typing import Any, List

from fastapi import Depends, FastAPI, HTTPException, Request, status

from app.auth import verify_token
from app.config import validate_environment
from app.database import build_select_query, execute_select
from app.schemas import QueryRequest, QueryResponse, FilterCondition
from app.semantic_maps import SEMANTIC_STATUS_FIELDS, resolve_status_filter

app = FastAPI(title="CW Secure SQL API", version="0.1.0")

# -----------------------
# Logging Setup
# -----------------------
logger = logging.getLogger("cw_sql_api")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


@app.on_event("startup")
def on_startup() -> None:
    try:
        validate_environment()
        logger.info("Startup validation succeeded.")
    except Exception as e:
        logger.error(f"Startup validation failed: {e}")
        raise


# ✅ FIXED VERSION
def apply_semantic_filters(request_body: QueryRequest) -> QueryRequest:
