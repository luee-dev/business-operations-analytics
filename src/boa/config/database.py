from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from boa.config.settings import settings


def get_database_url() -> URL:
    return URL.create(
        drivername="postgresql+psycopg",
        username=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        database=settings.POSTGRES_DB,
    )


engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,
)


def test_connection() -> bool:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar_one()

    return result == 1
