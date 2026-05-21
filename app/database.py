from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from app.config import settings


def get_connection_string() -> str:
    return (
        f"mssql+pyodbc://{settings.DB_USERNAME}:{settings.DB_PASSWORD}"
        f"@{settings.DB_SERVER}/{settings.DB_DATABASE}"
        f"?driver={settings.DB_DRIVER.replace(' ', '+')}"
        "&TrustServerCertificate=yes"
    )


def get_engine() -> Engine:
    connection_string = get_connection_string()

    engine = create_engine(
        connection_string,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

    return engine