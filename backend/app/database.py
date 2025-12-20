from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for getting database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    # Import models to register them with SQLAlchemy's metadata
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    if "users" in inspector.get_table_names():
        existing_columns = {col["name"] for col in inspector.get_columns("users")}
        statements = []
        added_gemini_model = False
        if "encrypted_gemini_api_key" not in existing_columns:
            statements.append("ALTER TABLE users ADD COLUMN encrypted_gemini_api_key TEXT")
        if "gemini_key_updated_at" not in existing_columns:
            statements.append("ALTER TABLE users ADD COLUMN gemini_key_updated_at TIMESTAMP")
        if "gemini_model" not in existing_columns:
            statements.append("ALTER TABLE users ADD COLUMN gemini_model TEXT")
            added_gemini_model = True

        if statements:
            with engine.begin() as connection:
                for statement in statements:
                    connection.execute(text(statement))

        if "gemini_model" in existing_columns or added_gemini_model:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE users SET gemini_model = 'gemini-2.0-flash' "
                        "WHERE gemini_model IS NULL"
                    )
                )
