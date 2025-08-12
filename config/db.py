from sqlmodel import Session, SQLModel, create_engine
from config.settings import settings

# Use DATABASE_URL from environment if available, otherwise use default SQLite URL
sqlite_file_name = "data.db"
default_sqlite_url = f"sqlite:///{sqlite_file_name}"
database_url = settings.DATABASE_URL or default_sqlite_url


def get_engine():
    connect_args = {"check_same_thread": False}
    if database_url.startswith("sqlite"):
        return create_engine(database_url, connect_args=connect_args)
    else:
        return create_engine(database_url)


engine = get_engine()


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_db_connection():
    with Session(engine) as session:
        yield session
